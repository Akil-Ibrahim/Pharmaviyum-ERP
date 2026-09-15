"""
LangGraph state definition for the medical RAG pipeline.

Best practice 2026:
- TypedDict for LangGraph compatibility
- Annotated reducers where list fields need append semantics
- Keep intermediate retrieval artifacts explicit for debugging and streaming
"""

from __future__ import annotations

from operator import add
from typing import Annotated, Literal, TypedDict

from .schemas import QueryContext, RetrievalResult


class RAGState(TypedDict):
    """
    Shared state across all nodes of the LangGraph RAG pipeline.

    Flow:
      transform_query -> retrieve -> grade_documents
        -> (rewrite_query -> retrieve)* -> compress -> generate -> guardrails
    """

    # ----- Input -----
    # Original user question
    question: str
    # Request context (country, language, halal_filter, patient_id, etc.)
    context: QueryContext

    # ----- Intermediate -----
    # Original question plus HyDE / multi-query / rewrite variants
    transformed_queries: list[str]
    # Raw hybrid-search hits (before relevance grading)
    retrieved: list[RetrievalResult]
    # Hits that passed the LLM relevance judge
    graded: list[RetrievalResult]
    # Compressed + reordered context string fed to the generator
    compressed_context: str
    # Result of the grade_documents node
    grade_decision: Literal["sufficient", "insufficient"]
    # How many times we already rewrote the query (loop guard)
    rewrite_count: int

    # ----- Output -----
    # Final natural-language answer
    answer: str | None
    # Safety / process warnings accumulated across nodes (append-only)
    warnings: Annotated[list[str], add]
    # Heuristic confidence in [0, 1]
    confidence: float
    # Which LLM produced the final answer
    model_used: str
    # End-to-end latency in milliseconds
    latency_ms: float
    # Token usage reported by the generator (if available)
    tokens_used: int
