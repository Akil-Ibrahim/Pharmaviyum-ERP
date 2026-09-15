"""pgvector-backed vector store with hybrid search (vector + BM25 + RRF)."""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any
from uuid import UUID

import numpy as np
from sqlalchemy import text

from src.pharmaviyum.core.logging import logger

from .schemas import Chunk, RetrievalResult


class PgVectorStore:
    """PostgreSQL + pgvector vector store."""

    _IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    def __init__(self, session_factory, table_name: str = "document_chunks", dimensions: int = 1024):
        if not self._IDENTIFIER_RE.fullmatch(table_name):
            raise ValueError("table_name must be a simple SQL identifier")
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        self.session_factory = session_factory
        self.table_name = table_name
        self.dimensions = dimensions

    async def initialize(self) -> None:
        """Initialize pgvector extension, table, and indexes."""
        async with self.session_factory() as session:
            await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            create_table_sql = f"""  # nosec B608: validated identifier and fixed SQL template
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id UUID PRIMARY KEY,
                    document_id UUID NOT NULL,
                    content TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    chunk_type VARCHAR(50) NOT NULL,
                    metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                    token_count INTEGER NOT NULL,
                    embedding vector({self.dimensions}),
                    created_at TIMESTAMP DEFAULT NOW(),
                    CONSTRAINT unique_chunk UNIQUE (document_id, chunk_index)
                )
            """
            await session.execute(text(create_table_sql))
            embedding_index_sql = f"""  # nosec B608: validated identifier and fixed SQL template
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_embedding
                ON {self.table_name} USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 200)
            """
            await session.execute(text(embedding_index_sql))
            metadata_index_sql = f"""  # nosec B608: validated identifier and fixed SQL template
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_metadata
                ON {self.table_name} USING gin (metadata)
            """
            await session.execute(text(metadata_index_sql))
            content_index_sql = f"""  # nosec B608: validated identifier and fixed SQL template
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_content_fts
                ON {self.table_name} USING gin (to_tsvector('english', content))
            """
            await session.execute(text(content_index_sql))
            await session.commit()
            logger.info("Vector store initialized: %s", self.table_name)

    async def upsert(self, chunks: list[Chunk], embeddings: list[list[float]]) -> int:
        """Batch upsert chunks with embeddings (idempotent)."""
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
                    "metadata": json.dumps(chunk.metadata),
                    "token_count": chunk.token_count,
                    "embedding": self._serialize_embedding(embedding),
                }
                for chunk, embedding in zip(chunks, embeddings)
            ]
            await session.execute(
                text(f"""  # nosec B608: table_name is validated as a SQL identifier
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

    async def vector_search(self, query_embedding: list[float], top_k: int = 10, filters: dict[str, Any] | None = None) -> list[RetrievalResult]:
        """Vector similarity search (cosine distance), always tenant scoped."""
        filter_clause, filter_params = self._build_filter_clause(filters)
        async with self.session_factory() as session:
            query_sql = text(f"""  # nosec B608: table_name and filter keys are validated
                SELECT id, document_id, content, chunk_index, chunk_type, metadata, token_count,
                       1 - (embedding <=> :query_embedding::vector) AS score
                FROM {self.table_name} {filter_clause}
                ORDER BY embedding <=> :query_embedding::vector LIMIT :top_k
            """)
            result = await session.execute(query_sql, {"query_embedding": self._serialize_embedding(query_embedding), "top_k": top_k, **filter_params})
            return [RetrievalResult(chunk=self._row_to_chunk(row), score=row.score, retrieval_method="vector") for row in result]

    async def bm25_search(self, query: str, top_k: int = 10, filters: dict[str, Any] | None = None) -> list[RetrievalResult]:
        """BM25 keyword search, always tenant scoped."""
        filter_clause, filter_params = self._build_filter_clause(filters)
        async with self.session_factory() as session:
            query_sql = text(f"""  # nosec B608: table_name and filter keys are validated
                SELECT id, document_id, content, chunk_index, chunk_type, metadata, token_count,
                       ts_rank(to_tsvector('english', content), plainto_tsquery('english', :query)) AS score
                FROM {self.table_name} {filter_clause}
                AND to_tsvector('english', content) @@ plainto_tsquery('english', :query)
                ORDER BY score DESC LIMIT :top_k
            """)
            result = await session.execute(query_sql, {"query": query, "top_k": top_k, **filter_params})
            return [RetrievalResult(chunk=self._row_to_chunk(row), score=row.score, retrieval_method="bm25") for row in result]

    async def hybrid_search(self, query: str, query_embedding: list[float], top_k: int = 10, filters: dict[str, Any] | None = None, reranker: str | None = None, rrf_k: int = 60) -> list[RetrievalResult]:
        """Hybrid vector + BM25 search with RRF and optional reranking."""
        self._require_tenant_filter(filters)
        vector_results, bm25_results = await asyncio.gather(
            self.vector_search(query_embedding, top_k=top_k * 2, filters=filters),
            self.bm25_search(query, top_k=top_k * 2, filters=filters),
        )
        fused = self._reciprocal_rank_fusion([vector_results, bm25_results], k=rrf_k)
        if reranker and fused:
            fused = await self._rerank(query, fused[: top_k * 3], reranker)
        return fused[:top_k]

    def _reciprocal_rank_fusion(self, result_lists: list[list[RetrievalResult]], k: int = 60) -> list[RetrievalResult]:
        scores: dict[str, float] = {}
        chunk_map: dict[str, RetrievalResult] = {}
        for results in result_lists:
            for rank, result in enumerate(results):
                chunk_id = str(result.chunk.id)
                scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank + 1)
                chunk_map[chunk_id] = result
        return [RetrievalResult(chunk=chunk_map[cid].chunk, score=scores[cid], retrieval_method="hybrid") for cid in sorted(scores, key=scores.get, reverse=True)]

    async def _rerank(self, query: str, results: list[RetrievalResult], model: str = "bge-reranker-v2-m3") -> list[RetrievalResult]:
        """Cross-encoder-style embedding reranking."""
        try:
            import ollama
            client = ollama.AsyncClient()
            scored = []
            for result in results:
                response = await client.embed(model=model, input=[query, result.chunk.content])
                score = float(np.dot(response["embeddings"][0], response["embeddings"][1]))
                scored.append((result, score))
            scored.sort(key=lambda item: item[1], reverse=True)
            return [RetrievalResult(chunk=r.chunk, score=r.score, retrieval_method="reranked", rerank_score=s) for r, s in scored]
        except Exception as exc:
            logger.warning("Reranking failed, using fused results: %s", exc)
            return results

    def _build_filter_clause(self, filters: dict[str, Any] | None) -> tuple[str, dict[str, Any]]:
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
        pharmacy_id = filters["pharmacy_id"]
        if not isinstance(pharmacy_id, int) or isinstance(pharmacy_id, bool) or pharmacy_id <= 0:
            raise ValueError("RAG retrieval requires a positive integer pharmacy_id")

    @staticmethod
    def _require_tenant_metadata(metadata: dict[str, Any]) -> None:
        """Fail closed if an ingested chunk has no tenant identity."""
        pharmacy_id = metadata.get("pharmacy_id")
        if not isinstance(pharmacy_id, int) or isinstance(pharmacy_id, bool) or pharmacy_id <= 0:
            raise ValueError("RAG ingestion requires a positive integer pharmacy_id")

    def _row_to_chunk(self, row) -> Chunk:
        return Chunk(id=UUID(row.id), document_id=UUID(row.document_id), content=row.content, chunk_index=row.chunk_index, chunk_type=row.chunk_type, metadata=json.loads(row.metadata) if isinstance(row.metadata, str) else row.metadata, token_count=row.token_count)

    def _serialize_embedding(self, embedding: list[float]) -> str:
        if len(embedding) != self.dimensions:
            raise ValueError(f"Expected embedding dimension {self.dimensions}, got {len(embedding)}")
        return "[" + ",".join(str(x) for x in embedding) + "]"
