"""
Structured Output Schemas for Agent Harness.

Best practice 2026:
- Strict Pydantic v2 validation for all agent responses
- Discriminated unions for different response types
- Source citations with confidence scores
- Machine-readable warnings for downstream systems
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class SourceCitation(BaseModel):
    """Single source cited in the agent's response."""

    model_config = ConfigDict(frozen=True)

    source_id: str
    source_type: Literal["rag_chunk", "tool_result", "static_db", "external_api"]
    content: str = Field(..., max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)
    relevance_score: float = Field(..., ge=0.0, le=1.0)


class ToolCallRecord(BaseModel):
    """Record of a single tool call made during agent execution."""

    model_config = ConfigDict(frozen=True)

    tool_name: str
    input_data: dict[str, Any]
    success: bool
    output_summary: str | None = None
    error: str | None = None
    latency_ms: float = 0.0


class Warning(BaseModel):
    """Structured warning for downstream systems (UI, audit, alerts)."""

    model_config = ConfigDict(frozen=True)

    code: str  # e.g., "dosage_unverified", "safety_block", "halal_flagged"
    severity: Literal["info", "warning", "critical"]
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """
    Structured output from the Pharmacist Agent.

    This is the canonical response format returned by AgentHarness.run().
    All downstream systems (FastAPI endpoints, UI, audit logs) consume this schema.
    """

    model_config = ConfigDict(frozen=True)

    # Core response
    response_id: UUID = Field(default_factory=uuid4)
    session_id: str
    query: str
    answer: str

    # Provenance
    sources: list[SourceCitation] = Field(default_factory=list)
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)

    # Quality indicators
    confidence: float = Field(..., ge=0.0, le=1.0)
    requires_human_review: bool = False
    escalation_reason: str | None = None

    # Safety & compliance
    warnings: list[Warning] = Field(default_factory=list)
    safety_score: float = Field(..., ge=0.0, le=1.0)

    # Metadata
    model_used: str
    total_latency_ms: float
    total_tokens_used: int = 0
    cache_hit: bool = False
    trace_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def is_safe(self) -> bool:
        """Response is safe if safety_score >= 0.9 and no critical warnings."""
        has_critical = any(w.severity == "critical" for w in self.warnings)
        return self.safety_score >= 0.9 and not has_critical

    @property
    def warning_codes(self) -> list[str]:
        """Extract warning codes for quick filtering."""
        return [w.code for w in self.warnings]

    def to_api_response(self) -> dict[str, Any]:
        """Convert to API-friendly dict (excludes internal fields)."""
        return {
            "response_id": str(self.response_id),
            "answer": self.answer,
            "sources": [s.model_dump() for s in self.sources],
            "warnings": [w.model_dump() for w in self.warnings],
            "confidence": self.confidence,
            "requires_human_review": self.requires_human_review,
            "safety_score": self.safety_score,
            "cache_hit": self.cache_hit,
            "latency_ms": self.total_latency_ms,
        }


class StreamingEvent(BaseModel):
    """Event for SSE streaming of agent execution."""

    model_config = ConfigDict(frozen=True)

    event_type: Literal[
        "start",
        "status",
        "tool_call",
        "tool_result",
        "token",
        "warning",
        "answer",
        "complete",
        "error",
    ]
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
