"""
RAG Pipeline Module — End-to-end Retrieval-Augmented Generation.

Best practice 2026:
- Clean public API via __all__
- Lazy imports to avoid circular dependencies
- Type-safe exports for IDE autocompletion

Public API:
    - RAGPipeline: Main orchestrator (ingest + query + stream)
    - MedicalChunker: Domain-aware chunking (vi/en/th/id)
    - PgVectorStore: pgvector-backed hybrid search
    - EmbeddingsFactory: Create embeddings providers
    - OllamaEmbeddings: Local embeddings via Ollama
    - CachedEmbeddings: Redis-cached embeddings wrapper
    - Document, Chunk, RetrievalResult, RAGResponse, QueryContext: Schemas

Usage:
    from src.pharmaviyum.ai.rag import RAGPipeline, Document, QueryContext
    
    pipeline = RAGPipeline(vector_store, embeddings, llm)
    await pipeline.ingest([document])
    response = await pipeline.query("drug interactions?", context)
"""
from .schemas import (
    Document,
    Chunk,
    RetrievalResult,
    RAGResponse,
    QueryContext,
)
from .chunking import MedicalChunker
from .vector_store import PgVectorStore
from .embeddings import (
    EmbeddingsFactory,
    EmbeddingsProvider,
    OllamaEmbeddings,
    CachedEmbeddings,
)
from .pipeline import RAGPipeline

__all__ = [
    # Pipeline
    "RAGPipeline",
    # Chunking
    "MedicalChunker",
    # Vector store
    "PgVectorStore",
    # Embeddings
    "EmbeddingsFactory",
    "EmbeddingsProvider",
    "OllamaEmbeddings",
    "CachedEmbeddings",
    # Schemas
    "Document",
    "Chunk",
    "RetrievalResult",
    "RAGResponse",
    "QueryContext",
]
