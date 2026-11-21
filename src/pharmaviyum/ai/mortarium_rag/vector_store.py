"""pgvector-backed vector store with hybrid search (vector + BM25 + RRF)."""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import Row

from src.pharmaviyum.core.logging import logger

from .ports import RerankerPort
from .schemas import CanonicalMetadata, Chunk, RetrievalResult


class PgVectorStore:
    """PostgreSQL + pgvector vector store with fail-closed tenant scope."""

    _IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    def __init__(
        self,
        session_factory: Any,
        table_name: str = "document_chunks",
        dimensions: int = 1024,
        reranker: RerankerPort | None = None,
    ) -> None:
        if not self._IDENTIFIER_RE.fullmatch(table_name):
            raise ValueError("table_name must be a simple SQL identifier")
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        self.session_factory = session_factory
        self.table_name = table_name
        self.dimensions = dimensions
        self.reranker = reranker

    async def initialize(self) -> None:
        """Verify the Alembic-managed pgvector schema without issuing DDL."""
        async with self.session_factory() as session:
            result = await session.execute(
                text("""
                    SELECT
                        to_regclass(:table_name) IS NOT NULL AS table_exists,
                        to_regtype('vector') IS NOT NULL AS vector_type_exists,
                        (
                            SELECT attribute.atttypmod
                            FROM pg_attribute AS attribute
                            WHERE attribute.attrelid = to_regclass(:table_name)
                              AND attribute.attname = 'embedding'
                              AND NOT attribute.attisdropped
                        ) AS embedding_dimensions,
                        COALESCE(
                            (
                                SELECT array_agg(indexname)
                                FROM pg_indexes
                                WHERE schemaname = (
                                      SELECT namespace.nspname
                                      FROM pg_class AS relation
                                      JOIN pg_namespace AS namespace
                                        ON namespace.oid = relation.relnamespace
                                      WHERE relation.oid = to_regclass(:table_name)
                                  )
                                  AND tablename = :table_name
                            ),
                            ARRAY[]::text[]
                        ) AS index_names
                    """),
                {
                    "table_name": self.table_name,
                },
            )
            schema = result.one()

        if not schema.table_exists:
            raise RuntimeError(
                f"pgvector table {self.table_name} is missing from the active search path; "
                "apply the Alembic database migrations before enabling RAG."
            )
        if not schema.vector_type_exists:
            raise RuntimeError(
                "PostgreSQL vector type is missing; apply the pgvector Alembic migration."
            )
        if schema.embedding_dimensions != self.dimensions:
            raise RuntimeError(
                "pgvector dimension mismatch: "
                f"configured={self.dimensions}, database={schema.embedding_dimensions}."
            )

        required_indexes = {
            f"idx_{self.table_name}_embedding",
            f"idx_{self.table_name}_metadata",
            f"idx_{self.table_name}_pharmacy_id",
            f"idx_{self.table_name}_content_fts",
            f"idx_{self.table_name}_content_fts_simple",
        }
        existing_indexes = set(schema.index_names or ())
        missing_indexes = sorted(required_indexes - existing_indexes)
        if missing_indexes:
            raise RuntimeError(
                "pgvector schema is missing required indexes: "
                + ", ".join(missing_indexes)
                + ". Apply the Alembic database migrations."
            )

        logger.info("Verified Alembic-managed pgvector schema: %s", self.table_name)

    async def upsert(self, chunks: list[Chunk], embeddings: list[list[float]]) -> int:
        """Batch upsert chunks after canonical metadata validation."""
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have same length")
        for chunk in chunks:
            self._require_tenant_metadata(chunk.metadata)

        async with self.session_factory() as session:
            values = [
                {
                    "id": str(chunk.id),
                    "document_id": str(chunk.document_id),
                    "content": chunk.content,
                    "chunk_index": chunk.chunk_index,
                    "chunk_type": chunk.chunk_type,
                    "metadata": self._serialize_metadata(chunk.metadata),
                    "token_count": chunk.token_count,
                    "embedding": self._serialize_embedding(embedding),
                }
                for chunk, embedding in zip(chunks, embeddings)
            ]
            await session.execute(
                # nosec B608: table_name is validated as a SQL identifier
                text(f"""
                INSERT INTO {self.table_name}
                (id, document_id, content, chunk_index, chunk_type, metadata, token_count, embedding)
                VALUES (:id, :document_id, :content, :chunk_index, :chunk_type, :metadata, :token_count, :embedding)
                ON CONFLICT (document_id, chunk_index)
                DO UPDATE SET content = EXCLUDED.content, metadata = EXCLUDED.metadata,
                              embedding = EXCLUDED.embedding, token_count = EXCLUDED.token_count
                """),
                values,
            )
            await session.commit()
            logger.info("Upserted %s chunks", len(chunks))
            return len(chunks)

    async def vector_search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        """Vector similarity search, always tenant scoped."""
        filter_clause, filter_params = self._build_filter_clause(filters)
        async with self.session_factory() as session:
            # nosec B608: table_name and filter keys are validated
            query_sql = text(f"""
                SELECT id, document_id, content, chunk_index, chunk_type, metadata, token_count,
                       1 - (embedding <=> CAST(:query_embedding AS vector)) AS score
                FROM {self.table_name} {filter_clause}
                ORDER BY embedding <=> CAST(:query_embedding AS vector) LIMIT :top_k
            """)
            result = await session.execute(
                query_sql,
                {
                    "query_embedding": self._serialize_embedding(query_embedding),
                    "top_k": top_k,
                    **filter_params,
                },
            )
            return [
                RetrievalResult(
                    chunk=self._row_to_chunk(row),
                    score=max(0.0, min(1.0, float(row.score))),
                    retrieval_method="vector",
                )
                for row in result
            ]

    async def bm25_search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
        language: str = "en",
    ) -> list[RetrievalResult]:
        """Keyword search with a safe language-specific PostgreSQL text-search config."""
        filter_clause, filter_params = self._build_filter_clause(filters)
        # PostgreSQL has robust built-in stemming for English. Its "simple"
        # configuration is a safer multilingual tokenizer fallback than English
        # stemming for languages without a built-in PostgreSQL dictionary.
        language_code = language.lower().split("-", maxsplit=1)[0]
        text_search_config = "english" if language_code == "en" else "simple"
        async with self.session_factory() as session:
            query_sql = text(f"""
                SELECT id, document_id, content, chunk_index, chunk_type, metadata, token_count,
                       ts_rank(
                           to_tsvector('{text_search_config}', content),
                           plainto_tsquery('{text_search_config}', :query)
                       ) AS score
                FROM {self.table_name} {filter_clause}
                AND to_tsvector('{text_search_config}', content)
                    @@ plainto_tsquery('{text_search_config}', :query)
                ORDER BY score DESC LIMIT :top_k
            """)
            result = await session.execute(
                query_sql,
                {"query": query, "top_k": top_k, **filter_params},
            )
            return [
                RetrievalResult(
                    chunk=self._row_to_chunk(row),
                    score=max(0.0, min(1.0, float(row.score))),
                    retrieval_method="bm25",
                )
                for row in result
            ]

    async def hybrid_search(
        self,
        query: str,
        query_embedding: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
        reranker: RerankerPort | None = None,
        rrf_k: int = 60,
    ) -> list[RetrievalResult]:
        """Hybrid vector + keyword search with optional typed reranking."""
        self._require_tenant_filter(filters)
        assert filters is not None
        search_language = str(filters.get("_search_language", "en"))
        metadata_filters = {
            key: value for key, value in filters.items() if key != "_search_language"
        }
        vector_results, bm25_results = await asyncio.gather(
            self.vector_search(
                query_embedding, top_k=top_k * 2, filters=metadata_filters
            ),
            self.bm25_search(
                query,
                top_k=top_k * 2,
                filters=metadata_filters,
                language=search_language,
            ),
        )
        fused = self._reciprocal_rank_fusion([vector_results, bm25_results], k=rrf_k)
        active_reranker = reranker or self.reranker
        if active_reranker and fused:
            try:
                fused = await active_reranker.rerank(
                    query=query, results=fused[: top_k * 3], top_k=top_k
                )
            except Exception as exc:
                logger.warning(
                    "Reranking failed; using fused retrieval results",
                    extra={"error_type": type(exc).__name__},
                )
        return fused[:top_k]

    def _reciprocal_rank_fusion(
        self, result_lists: list[list[RetrievalResult]], k: int = 60
    ) -> list[RetrievalResult]:
        scores: dict[str, float] = {}
        chunk_map: dict[str, RetrievalResult] = {}
        for results in result_lists:
            for rank, result in enumerate(results):
                chunk_id = str(result.chunk.id)
                scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank + 1)
                chunk_map[chunk_id] = result

        ordered_ids = sorted(
            scores, key=lambda chunk_id: scores[chunk_id], reverse=True
        )
        return [
            RetrievalResult(
                chunk=chunk_map[cid].chunk,
                score=min(1.0, scores[cid]),
                retrieval_method="hybrid",
            )
            for cid in ordered_ids
        ]

    def _build_filter_clause(
        self, filters: dict[str, Any] | None
    ) -> tuple[str, dict[str, Any]]:
        """Build a parameterized WHERE clause with a mandatory tenant boundary."""
        self._require_tenant_filter(filters)
        assert filters is not None
        clauses: list[str] = []
        params: dict[str, Any] = {}
        for index, (key, value) in enumerate(filters.items()):
            if not self._IDENTIFIER_RE.fullmatch(key):
                raise ValueError(f"Invalid metadata filter key: {key!r}")
            param = f"filter_{index}"
            if isinstance(value, bool):
                clauses.append(f"(metadata ->> '{key}')::boolean = :{param}")
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                clauses.append(f"(metadata ->> '{key}')::numeric = :{param}")
            else:
                clauses.append(f"metadata ->> '{key}' = :{param}")
            params[param] = value
        return "WHERE " + " AND ".join(clauses), params

    @staticmethod
    def _require_tenant_filter(filters: dict[str, Any] | None) -> None:
        """Fail closed if retrieval is attempted without a pharmacy tenant."""
        if not filters or "pharmacy_id" not in filters:
            raise ValueError("RAG retrieval requires a pharmacy_id tenant filter")
        PgVectorStore._require_pharmacy_id(filters["pharmacy_id"])

        access_level = filters.get("access_level")
        patient_id = filters.get("patient_id")
        if patient_id is not None and (
            not isinstance(patient_id, int)
            or isinstance(patient_id, bool)
            or patient_id <= 0
        ):
            raise ValueError("RAG retrieval requires a positive integer patient_id")
        if patient_id is not None and access_level != "patient":
            raise ValueError("RAG patient_id filter requires access_level='patient'")
        if not isinstance(access_level, str) or access_level not in {
            "public",
            "pharmacy",
            "patient",
        }:
            raise ValueError(
                "RAG retrieval requires an explicit valid access_level filter"
            )
        if access_level == "patient" and patient_id is None:
            raise ValueError(
                "Patient-level RAG retrieval requires an exact patient_id filter"
            )

    @staticmethod
    def _require_tenant_metadata(metadata: dict[str, Any]) -> None:
        """Fail closed if an ingested chunk has no canonical tenant metadata."""
        if "pharmacy_id" not in metadata:
            raise ValueError("RAG ingestion requires pharmacy_id tenant metadata")
        PgVectorStore._require_pharmacy_id(metadata["pharmacy_id"])
        CanonicalMetadata.model_validate(metadata)

    @staticmethod
    def _require_pharmacy_id(pharmacy_id: Any) -> None:
        """Validate a tenant identifier independently from retrieval scope."""
        if (
            not isinstance(pharmacy_id, int)
            or isinstance(pharmacy_id, bool)
            or pharmacy_id <= 0
        ):
            raise ValueError("RAG scope requires a positive integer pharmacy_id")

    @staticmethod
    def _serialize_metadata(metadata: dict[str, Any]) -> str:
        """Persist canonical fields first so extension fields cannot override them."""
        canonical = CanonicalMetadata.model_validate(metadata).model_dump(mode="json")
        extra = {
            key: value
            for key, value in metadata.items()
            if key not in CanonicalMetadata.model_fields
        }
        return json.dumps({**canonical, **extra})

    def _row_to_chunk(self, row: Row[Any]) -> Chunk:
        return Chunk(
            id=UUID(str(row.id)),
            document_id=UUID(str(row.document_id)),
            content=str(row.content),
            chunk_index=int(row.chunk_index),
            chunk_type=row.chunk_type,
            metadata=(
                json.loads(row.metadata)
                if isinstance(row.metadata, str)
                else dict(row.metadata)
            ),
            token_count=int(row.token_count),
        )

    def _serialize_embedding(self, embedding: list[float]) -> str:
        if len(embedding) != self.dimensions:
            raise ValueError(
                f"Expected embedding dimension {self.dimensions}, got {len(embedding)}"
            )
        return "[" + ",".join(str(x) for x in embedding) + "]"
