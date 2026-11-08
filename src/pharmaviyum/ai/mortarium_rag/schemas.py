"""RAG pipeline schemas and explicit retrieval contracts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CanonicalMetadata(BaseModel):
    """Canonical metadata persisted with every searchable chunk."""

    model_config = ConfigDict(extra="allow", frozen=True)

    pharmacy_id: int = Field(..., gt=0)
    source: str = Field(..., min_length=1)
    version: str | None = None
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    access_level: Literal["public", "pharmacy", "patient"] = "pharmacy"
    patient_id: int | None = Field(default=None, gt=0)
    country: str | None = Field(default=None, min_length=2, max_length=8)
    language: str = Field(default="en", min_length=2, max_length=8)
    category: str | None = None
    doc_type: str | None = None

    @model_validator(mode="after")
    def validate_effective_window(self) -> "CanonicalMetadata":
        if self.access_level == "patient" and self.patient_id is None:
            raise ValueError("patient access_level requires patient_id")
        if (
            self.effective_from is not None
            and self.effective_to is not None
            and self.effective_to < self.effective_from
        ):
            raise ValueError("effective_to cannot be earlier than effective_from")
        return self


class Document(BaseModel):
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
    country: str | None = None
    language: str = "en"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Chunk(BaseModel):
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
    model_config = ConfigDict(frozen=True)
    chunk: Chunk
    score: float = Field(..., ge=0.0)
    retrieval_method: Literal["vector", "bm25", "hybrid", "reranked"]
    rerank_score: float | None = None


class SourceCitation(BaseModel):
    model_config = ConfigDict(frozen=True)
    citation_id: str
    document_id: UUID
    chunk_id: UUID
    source: str
    version: str | None = None
    retrieval_score: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class RAGResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    answer: str
    sources: list[RetrievalResult] = Field(default_factory=list)
    citations: list[SourceCitation] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)
    warnings: list[str] = Field(default_factory=list)
    model_used: str
    latency_ms: float
    tokens_used: int = 0

    @model_validator(mode="after")
    def bind_source_citations(self) -> "RAGResponse":
        if self.citations or not self.sources:
            return self
        citations = [
            SourceCitation(
                citation_id=f"src-{source.chunk.id}",
                document_id=source.chunk.document_id,
                chunk_id=source.chunk.id,
                source=str(source.chunk.metadata.get("source", "knowledge_base")),
                version=(
                    str(source.chunk.metadata["version"])
                    if source.chunk.metadata.get("version") is not None
                    else None
                ),
                retrieval_score=(
                    source.rerank_score
                    if source.rerank_score is not None
                    else source.score
                ),
                metadata=dict(source.chunk.metadata),
            )
            for source in self.sources
        ]
        object.__setattr__(self, "citations", citations)
        return self


class QueryContext(BaseModel):
    """Immutable, authenticated AI request context."""

    model_config = ConfigDict(frozen=True)
    user_id: str = Field(..., min_length=1, max_length=128)
    pharmacy_id: int = Field(..., gt=0)
    patient_id: int | None = Field(default=None, gt=0)
    prescription_id: int | None = None
    country: str | None = None
    language: str = "en"
    category: str | None = None
    halal_filter: bool = False
    force_fresh: bool = False
    max_tokens: int = Field(default=1024, gt=0, le=8192)
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
