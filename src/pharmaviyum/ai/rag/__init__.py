"""
RAG Pipeline Module — End-to-end Retrieval-Augmented Generation.

Public API:
    Pipeline:
    - RAGPipeline: Main orchestrator
    - IngestionOrchestrator: Full ingestion with dedup/versioning
    
    Retrieval Enhancements:
    - QueryTransformer: HyDE, multi-query, decomposition
    - ContextualCompressor: Sentence-level compression + Lost-in-the-Middle mitigation
    
    Components:
    - MedicalChunker: Domain-aware chunking
    - PgVectorStore: pgvector with HNSW + hybrid search + RRF
    - MultiLanguageEmbeddingRouter: Language-aware model selection
    - EmbeddingQualityEvaluator: Retrieval metrics
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
from .query_transformer import QueryTransformer, QueryVariation
from .contextual_compression import ContextualCompressor, CompressedContext

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
    # Retrieval enhancements
    "QueryTransformer",
    "QueryVariation",
    "ContextualCompressor",
    "CompressedContext",
    # Schemas
    "Document",
    "Chunk",
    "RetrievalResult",
    "RAGResponse",
    "QueryContext",
]
