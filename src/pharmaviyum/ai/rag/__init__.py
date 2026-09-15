"""
RAG Pipeline Module — End-to-end Retrieval-Augmented Generation.

Public API:
    Pipeline:
    - RAGPipeline: Main orchestrator (linear / ingest path)
    - LangGraphRAG: Query path orchestrated by LangGraph StateGraph
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

    LangGraph:
    - RAGState: TypedDict state for the RAG graph
"""

from .chunking import MedicalChunker
from .contextual_compression import CompressedContext, ContextualCompressor
from .embeddings import (CachedEmbeddings, EmbeddingsFactory,
                         EmbeddingsProvider, OllamaEmbeddings)
from .embeddings_multilang import (LANGUAGE_MODEL_MAP,
                                   MultiLanguageEmbeddingRouter)
# LangGraph-based query path
from .graph import LangGraphRAG
from .ingestion import IngestionOrchestrator
from .pipeline import RAGPipeline
from .preprocessing import DocumentPreprocessor
from .quality_metrics import (DriftDetector, EmbeddingDriftReport,
                              EmbeddingQualityEvaluator, RetrievalMetrics)
from .query_transformer import QueryTransformer, QueryVariation
from .schemas import (Chunk, Document, QueryContext, RAGResponse,
                      RetrievalResult)
from .state import RAGState
from .vector_store import PgVectorStore

__all__ = [
    # Pipeline
    "RAGPipeline",
    "LangGraphRAG",
    "RAGState",
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
