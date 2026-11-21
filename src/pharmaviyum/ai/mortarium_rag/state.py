"""Typed LangGraph state for the medical RAG pipeline."""

from __future__ import annotations

from operator import add
from typing import Annotated, Literal, TypedDict

from .schemas import QueryContext, RetrievalResult


class RAGState(TypedDict):
    """Shared state across all nodes of the tenant-scoped RAG graph."""

    question: str
    context: QueryContext
    transformed_queries: list[str]
    retrieved: list[RetrievalResult]
    graded: list[RetrievalResult]
    compressed_context: str
    grade_decision: Literal["sufficient", "insufficient"]
    rewrite_count: int
    input_blocked: bool
    answer: str | None
    warnings: Annotated[list[str], add]
    confidence: float
    model_used: str
    latency_ms: float
    tokens_used: int
