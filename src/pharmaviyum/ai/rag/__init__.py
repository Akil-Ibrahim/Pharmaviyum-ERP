"""RAG pipeline module — end-to-end retrieval-augmented generation."""

from .chunking import MedicalChunker
from .contextual_compression import CompressedContext, ContextualCompressor
from .embeddings import CachedEmbeddings, EmbeddingsFactory, EmbeddingsProvider, OllamaEmbeddings
from .embeddings_multilang import LANGUAGE_MODEL_MAP, MultiLanguageEmbeddingRouter
from .graph import LangGraphRAG
from .ingestion import IngestionOrchestrator
from .pipeline import RAGPipeline
from .ports import RerankerPort
from .preprocessing import DocumentPreprocessor
from .quality_metrics import DriftDetector, EmbeddingDriftReport, EmbeddingQualityEvaluator, RetrievalMetrics
from .query_transformer import QueryTransformer, QueryVariation
from .schemas import CanonicalMetadata, Chunk, Document, QueryContext, RAGResponse, RetrievalResult, SourceCitation
from .state import RAGState
from .vector_store import PgVectorStore

__all__ = [
    "RAGPipeline",
    "LangGraphRAG",
    "RAGState",
    "IngestionOrchestrator",
    "MedicalChunker",
    "PgVectorStore",
    "RerankerPort",
    "EmbeddingsFactory",
    "EmbeddingsProvider",
    "OllamaEmbeddings",
    "CachedEmbeddings",
    "MultiLanguageEmbeddingRouter",
    "LANGUAGE_MODEL_MAP",
    "EmbeddingQualityEvaluator",
    "DriftDetector",
    "RetrievalMetrics",
    "EmbeddingDriftReport",
    "DocumentPreprocessor",
    "QueryTransformer",
    "QueryVariation",
    "ContextualCompressor",
    "CompressedContext",
    "CanonicalMetadata",
    "Document",
    "Chunk",
    "RetrievalResult",
    "SourceCitation",
    "RAGResponse",
    "QueryContext",
]
