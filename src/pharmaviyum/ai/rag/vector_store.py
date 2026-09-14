"""pgvector-backed vector store with hybrid search (vector + BM25 + RRF)."""
from __future__ import annotations
import json
from typing import Any
from uuid import UUID
import numpy as np
from sqlalchemy import text
from .schemas import Chunk, RetrievalResult
from src.pharmaviyum.core.logging import logger


class PgVectorStore:
    """
    PostgreSQL + pgvector vector store.
    
    Features:
    - HNSW index (ef_construction=200, m=16)
    - Hybrid search (vector + BM25 + RRF fusion)
    - Metadata filtering
    - Cross-encoder reranking
    """
    
    def __init__(self, session_factory, table_name: str = "document_chunks", dimensions: int = 1024):
        self.session_factory = session_factory
        self.table_name = table_name
        self.dimensions = dimensions
    
    async def initialize(self) -> None:
        """Initialize pgvector extension, table, and indexes."""
        async with self.session_factory() as session:
            await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            
            await session.execute(text(f"""
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
            """))
            
            # HNSW index for fast vector search
            await session.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_embedding
                ON {self.table_name} USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 200)
            """))
            
            # GIN index for metadata queries
            await session.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_metadata
                ON {self.table_name} USING gin (metadata)
            """))
            
            # Full-text search index
            await session.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_content_fts
                ON {self.table_name} USING gin (to_tsvector('english', content))
            """))
            
            await session.commit()
            logger.info(f"Vector store initialized: {self.table_name}")
    
    async def upsert(self, chunks: list[Chunk], embeddings: list[list[float]]) -> int:
        """Batch upsert chunks with embeddings (idempotent)."""
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have same length")
        
        async with self.session_factory() as session:
            values = []
            for chunk, embedding in zip(chunks, embeddings):
                values.append({
                    "id": str(chunk.id),
                    "document_id": str(chunk.document_id),
                    "content": chunk.content,
                    "chunk_index": chunk.chunk_index,
                    "chunk_type": chunk.chunk_type,
                    "metadata": json.dumps(chunk.metadata),
                    "token_count": chunk.token_count,
                    "embedding": self._serialize_embedding(embedding),
                })
            
            await session.execute(text(f"""
                INSERT INTO {self.table_name}
                (id, document_id, content, chunk_index, chunk_type, metadata, token_count, embedding)
                VALUES
                (:id, :document_id, :content, :chunk_index, :chunk_type, :metadata, :token_count, :embedding)
                ON CONFLICT (document_id, chunk_index)
                DO UPDATE SET
                    content = EXCLUDED.content,
                    metadata = EXCLUDED.metadata,
                    embedding = EXCLUDED.embedding,
                    token_count = EXCLUDED.token_count
            """), values)
            
            await session.commit()
            logger.info(f"Upserted {len(chunks)} chunks")
            return len(chunks)
    
    async def vector_search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        """Vector similarity search (cosine distance)."""
        filter_clause = self._build_filter_clause(filters) if filters else ""
        
        async with self.session_factory() as session:
            query_sql = text(f"""
                SELECT
                    id, document_id, content, chunk_index, chunk_type,
                    metadata, token_count,
                    1 - (embedding <=> :query_embedding::vector) AS score
                FROM {self.table_name}
                {filter_clause}
                ORDER BY embedding <=> :query_embedding::vector
                LIMIT :top_k
            """)
            
            result = await session.execute(
                query_sql,
                {"query_embedding": self._serialize_embedding(query_embedding), "top_k": top_k, **(filters or {})},
            )
            
            return [
                RetrievalResult(chunk=self._row_to_chunk(row), score=row.score, retrieval_method="vector")
                for row in result
            ]
    
    async def bm25_search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        """BM25 keyword search (exact matches for drug names)."""
        filter_clause = self._build_filter_clause(filters) if filters else ""
        and_clause = "AND" if filter_clause else "WHERE"
        
        async with self.session_factory() as session:
            query_sql = text(f"""
                SELECT
                    id, document_id, content, chunk_index, chunk_type,
                    metadata, token_count,
                    ts_rank(to_tsvector('english', content), plainto_tsquery('english', :query)) AS score
                FROM {self.table_name}
                {filter_clause}
                {and_clause} to_tsvector('english', content) @@ plainto_tsquery('english', :query)
                ORDER BY score DESC
                LIMIT :top_k
            """)
            
            result = await session.execute(query_sql, {"query": query, "top_k": top_k, **(filters or {})})
            
            return [
                RetrievalResult(chunk=self._row_to_chunk(row), score=row.score, retrieval_method="bm25")
                for row in result
            ]
    
    async def hybrid_search(
        self,
        query: str,
        query_embedding: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
        reranker: str | None = None,
        rrf_k: int = 60,
    ) -> list[RetrievalResult]:
        """
        Hybrid search: vector + BM25 + RRF fusion + optional reranking.
        
        Best practice 2026:
        1. Vector search (semantic similarity)
        2. BM25 search (keyword matching)
        3. Reciprocal Rank Fusion (RRF)
        4. Cross-encoder reranking (optional, expensive but accurate)
        """
        import asyncio
        
        vector_results, bm25_results = await asyncio.gather(
            self.vector_search(query_embedding, top_k=top_k * 2, filters=filters),
            self.bm25_search(query, top_k=top_k * 2, filters=filters),
        )
        
        fused = self._reciprocal_rank_fusion([vector_results, bm25_results], k=rrf_k)
        
        if reranker and fused:
            fused = await self._rerank(query, fused[:top_k * 3], reranker)
        
        return fused[:top_k]
    
    def _reciprocal_rank_fusion(
        self,
        result_lists: list[list[RetrievalResult]],
        k: int = 60,
    ) -> list[RetrievalResult]:
        """RRF: score = Σ 1/(k + rank_i). Combines multiple ranked lists."""
        scores: dict[str, float] = {}
        chunk_map: dict[str, RetrievalResult] = {}
        
        for results in result_lists:
            for rank, result in enumerate(results):
                chunk_id = str(result.chunk.id)
                scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank + 1)
                chunk_map[chunk_id] = result
        
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        
        return [
            RetrievalResult(chunk=chunk_map[cid].chunk, score=scores[cid], retrieval_method="hybrid")
            for cid in sorted_ids
        ]
    
    async def _rerank(
        self,
        query: str,
        results: list[RetrievalResult],
        model: str = "bge-reranker-v2-m3",
    ) -> list[RetrievalResult]:
        """Cross-encoder reranking for improved accuracy."""
        try:
            import ollama
            client = ollama.AsyncClient()
            
            scored = []
            for result in results:
                response = await client.embed(model=model, input=[query, result.chunk.content])
                rerank_score = float(np.dot(response["embeddings"][0], response["embeddings"][1]))
                scored.append((result, rerank_score))
            
            scored.sort(key=lambda x: x[1], reverse=True)
            
            return [
                RetrievalResult(chunk=r.chunk, score=r.score, retrieval_method="reranked", rerank_score=s)
                for r, s in scored
            ]
        except Exception as e:
            logger.warning(f"Reranking failed, using fused results: {e}")
            return results
    
    def _build_filter_clause(self, filters: dict[str, Any]) -> str:
        """Build SQL WHERE clause from metadata filters."""
        if not filters:
            return ""
        
        clauses = []
        for key, value in filters.items():
            if isinstance(value, bool):
                clauses.append(f"(metadata->>'{key}')::boolean = {str(value).lower()}")
            elif isinstance(value, (int, float)):
                clauses.append(f"(metadata->>'{key}')::numeric = {value}")
            else:
                clauses.append(f"metadata->>'{key}' = '{value}'")
        
        return "WHERE " + " AND ".join(clauses) if clauses else ""
    
    def _row_to_chunk(self, row) -> Chunk:
        """Convert database row to Chunk."""
        return Chunk(
            id=UUID(row.id),
            document_id=UUID(row.document_id),
            content=row.content,
            chunk_index=row.chunk_index,
            chunk_type=row.chunk_type,
            metadata=json.loads(row.metadata) if isinstance(row.metadata, str) else row.metadata,
            token_count=row.token_count,
        )
    
    def _serialize_embedding(self, embedding: list[float]) -> str:
        """Serialize embedding to pgvector format."""
        return "[" + ",".join(str(x) for x in embedding) + "]"
