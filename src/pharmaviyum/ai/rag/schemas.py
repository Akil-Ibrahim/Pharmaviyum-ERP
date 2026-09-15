"""RAG Pipeline Schemas (Pydantic v2, frozen models)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class Document(BaseModel):
    """Input document for ingestion pipeline."""

    model_config = ConfigDict(frozen=True)
    id: UUID = Field(default_factory=uuid4)
    content: str = Field(..., min_length=1)
    source: str
    doc_type: Literal[
        "drug_info",
        "prescription",
        "guideline",
        "research_paper",
        "regulation",
        "patient_record",
    ]
    metadata: dict[str, Any] = Field(default_factory=dict)
    country: str = Field(default="VN")
    language: str = Field(default="vi")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Chunk(BaseModel):
    """Semantic chunk of a document."""

    model_config = ConfigDict(frozen=True)
    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    content: str = Field(..., min_length=1)
    chunk_index: int = Field(..., ge=0)
    chunk_type: Literal[
        "indications",
        "dosage",
        "contraindications",
        "interactions",
        "side_effects",
        "general",
    ] = "general"
    metadata: dict[str, Any] = Field(default_factory=dict)
    token_count: int = Field(..., ge=0)


class RetrievalResult(BaseModel):
    """Result from vector search."""

    model_config = ConfigDict(frozen=True)
    chunk: Chunk
    score: float = Field(..., ge=0.0, le=1.0)
    retrieval_method: Literal["vector", "bm25", "hybrid", "reranked"]
    rerank_score: float | None = None


class RAGResponse(BaseModel):
    """Final RAG pipeline response."""

    answer: str
    sources: list[RetrievalResult] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)
    warnings: list[str] = Field(default_factory=list)
    model_used: str
    latency_ms: float
    tokens_used: int = 0


class QueryContext(BaseModel):
    """Tenant-scoped context for a RAG query."""

    model_config = ConfigDict(frozen=True)

    # Required tenant boundary. AI/RAG must never retrieve across pharmacies.
    pharmacy_id: int
    patient_id: int | None = None
    prescription_id: int | None = None
    country: str = "VN"
    language: str = "vi"
    category: str | None = None
    halal_filter: bool = False
    force_fresh: bool = False
    max_tokens: int = Field(default=1024, gt=0, le=8192)
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
