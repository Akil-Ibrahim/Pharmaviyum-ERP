"""
RAG Pipeline Module — End-to-end Retrieval-Augmented Generation.

Public API:
    Pipeline:
    - RAGPipeline: Main orchestrator (ingest + query + stream)
    - IngestionOrchestrator: Full ingestion with dedup/versioning
    
    Components:
    - MedicalChunker: Domain-aware chunking (vi/en/th/id/ar)
    - PgVectorStore: pgvector with HNSW + hybrid search + RRF
    - MultiLanguageEmbeddingRouter: Language-aware model selection
    - EmbeddingQualityEvaluator: Retrieval metrics (recall@k, MRR, NDCG)
    - DriftDetector: Embedding quality drift monitoring
    
    Schemas:
    - Document, Chunk, RetrievalResult, RAGResponse, QueryContext
"""
from .schemas import (
    Document, Chunk, RetrievalResult, RAGResponse, QueryContext,
)
from .chunking import MedicalChunker
from .vector_store import PgVectorStore
from .embeddings import (
    EmbeddingsFactory, EmbeddingsProvider, OllamaEmbeddings, CachedEmbeddings,
)
from .embeddings_multilang import (
    MultiLanguageEmbeddingRouter, LANGUAGE_MODEL_MAP,
)
from .quality_metrics import (
    EmbeddingQualityEvaluator, DriftDetector,
    RetrievalMetrics, EmbeddingDriftReport,
)
from .pipeline import RAGPipeline
from .preprocessing import DocumentPreprocessor
from .ingestion import IngestionOrchestrator

__all__ = [
    # Pipeline
    "RAGPipeline",
    "IngestionOrchestrator",
    # Chunking
    "MedicalChunker",
    # Vector store
    "PgVectorStore",
    # Embeddings
    "EmbeddingsFactory",
    "EmbeddingsProvider",
    "OllamaEmbeddings",
    "CachedEmbeddings",
    "MultiLanguageEmbeddingRouter",
    "LANGUAGE_MODEL_MAP",
    # Quality
    "EmbeddingQualityEvaluator",
    "DriftDetector",
    "RetrievalMetrics",
    "EmbeddingDriftReport",
    # Preprocessing
    "DocumentPreprocessor",
    # Schemas
    "Document",
    "Chunk",
    "RetrievalResult",
    "RAGResponse",
    "QueryContext",
]
