from __future__ import annotations

import pytest

from src.pharmaviyum.ai.rag.graph import LangGraphRAG


@pytest.fixture
def rag() -> LangGraphRAG:
    """Build a lightweight instance without initializing external AI clients."""
    return LangGraphRAG.__new__(LangGraphRAG)


def test_route_after_grade_sufficient(rag: LangGraphRAG) -> None:
    state = {"grade_decision": "sufficient", "rewrite_count": 0}
    assert rag._route_after_grade(state) == "sufficient"


def test_route_after_grade_rewrites_until_budget_is_exhausted(
    rag: LangGraphRAG,
) -> None:
    assert (
        rag._route_after_grade({"grade_decision": "insufficient", "rewrite_count": 0})
        == "rewrite"
    )
    assert (
        rag._route_after_grade({"grade_decision": "insufficient", "rewrite_count": 1})
        == "rewrite"
    )
    assert (
        rag._route_after_grade({"grade_decision": "insufficient", "rewrite_count": 2})
        == "give_up"
    )


def test_thread_id_is_namespaced_and_unique_without_caller_id(
    rag: LangGraphRAG,
) -> None:
    assert rag._thread_id("conversation-123") == "rag:conversation-123"
    first = rag._thread_id(None)
    second = rag._thread_id(None)
    assert first.startswith("rag:")
    assert second.startswith("rag:")
    assert first != second


@pytest.mark.asyncio
async def test_no_answer_fails_closed(rag: LangGraphRAG) -> None:
    result = await rag.no_answer_node({})
    assert result["confidence"] == 0.0
    assert result["model_used"] == "none"
    assert result["tokens_used"] == 0
    assert "no_relevant_documents" in result["warnings"]
    assert "pharmacist" in result["answer"].lower()
