"""Ports used by the AI/RAG layer.

The RAG orchestration depends on these contracts rather than concrete
PostgreSQL/Ollama adapters. This keeps LangGraph inside the AI layer and
prevents infrastructure details from leaking into the orchestration boundary.
"""

from __future__ import annotations

from typing import Any, Protocol, Sequence

from .schemas import RetrievalResult


class RetrieverPort(Protocol):
    """Retrieve evidence for an AI query."""

    async def hybrid_search(
        self,
        *,
        query: str,
        query_embedding: Sequence[float],
        top_k: int,
        filters: dict[str, Any],
    ) -> list[RetrievalResult]:
        ...


class EmbeddingsPort(Protocol):
    """Create embeddings for retrieval queries."""

    async def embed(self, text: str) -> list[float]:
        ...


class LLMPort(Protocol):
    """Minimal async LLM contract required by the RAG graph."""

    async def ainvoke(self, prompt: str) -> Any:
        ...


class GuardrailsPort(Protocol):
    """Optional post-generation safety boundary."""

    async def post_process(self, answer: str, context: Any) -> Any:
        ...


class CheckpointerPort(Protocol):
    """LangGraph checkpoint persistence contract."""


__all__ = [
    "CheckpointerPort",
    "EmbeddingsPort",
    "GuardrailsPort",
    "LLMPort",
    "RetrieverPort",
]
