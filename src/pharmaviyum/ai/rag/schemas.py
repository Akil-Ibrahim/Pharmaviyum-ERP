"""RAG Pipeline Schemas (Pydantic v2, frozen models)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


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
    country: str = "VN"
    language: str = "vi"
    created_at: datetime = Field(default_factory=datetime.utcnow)


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
    score: float = Field(..., ge=0.0, le=1.0)
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
                source=str(
                    source.chunk.metadata.get(
                        "source", source.chunk.metadata.get("source_uri", "knowledge_base")
                    )
                ),
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
        return self.model_copy(update={"citations": citations})


class QueryContext(BaseModel):
    """Immutable, authenticated AI request context."""

    model_config = ConfigDict(frozen=True)
    user_id: str
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
