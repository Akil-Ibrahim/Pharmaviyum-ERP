"""Ports used by the AI/RAG layer."""

from __future__ import annotations

from typing import Any, Protocol

from langchain_core.runnables import RunnableConfig

from .schemas import RetrievalResult


class RetrieverPort(Protocol):
    async def hybrid_search(
        self,
        *,
        query: str,
        query_embedding: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]: ...


class RerankerPort(Protocol):
    """Dedicated reranker contract; implementation is injectable infrastructure."""

    async def rerank(
        self, *, query: str, results: list[RetrievalResult], top_k: int
    ) -> list[RetrievalResult]: ...


class EmbeddingsPort(Protocol):
    async def embed(self, text: str) -> list[float]: ...


class LLMPort(Protocol):
    async def ainvoke(
        self, input: Any, config: RunnableConfig | None = None, **kwargs: Any
    ) -> Any: ...


class GuardrailsPort(Protocol):
    async def pre_process(self, user_input: str) -> Any: ...

    async def post_process(
        self,
        answer: str,
        question: str,
        sources: list[RetrievalResult] | None = None,
    ) -> Any: ...


class CheckpointerPort(Protocol):
    """LangGraph checkpoint persistence contract."""


__all__ = [
    "CheckpointerPort",
    "EmbeddingsPort",
    "GuardrailsPort",
    "LLMPort",
    "RerankerPort",
    "RetrieverPort",
]
