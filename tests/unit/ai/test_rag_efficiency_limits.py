"""Regression tests for configurable Mortarium RAG efficiency limits."""

from unittest.mock import MagicMock

import pytest

from src.pharmaviyum.ai.mortarium_rag.graph import LangGraphRAG


def _build_rag(**overrides) -> LangGraphRAG:
    options = {
        "vector_store": MagicMock(),
        "embeddings": MagicMock(),
        "llm": MagicMock(),
        "checkpointer": MagicMock(),
    }
    options.update(overrides)
    return LangGraphRAG(**options)


def test_rag_limits_can_be_configured() -> None:
    rag = _build_rag(
        retrieval_top_k=5,
        max_context_docs=5,
        max_rewrites=1,
        max_query_variations=1,
        enable_multi_query=False,
        enable_hyde=False,
    )

    assert rag.retrieval_top_k == 5
    assert rag.max_context_docs == 5
    assert rag.max_rewrites == 1
    assert rag.max_query_variations == 1
    assert rag.enable_multi_query is False
    assert rag.enable_hyde is False


@pytest.mark.parametrize(
    "overrides",
    [
        {"retrieval_top_k": 0},
        {"max_context_docs": 0},
        {"max_rewrites": -1},
        {"max_query_variations": 0},
    ],
)
def test_rag_rejects_invalid_efficiency_limits(overrides: dict[str, int]) -> None:
    with pytest.raises(ValueError):
        _build_rag(**overrides)
