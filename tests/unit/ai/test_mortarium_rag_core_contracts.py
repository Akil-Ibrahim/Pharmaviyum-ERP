"""Regression tests for core Mortarium RAG contracts."""

from types import SimpleNamespace

import pytest

from src.pharmaviyum.ai.mortarium_rag.graph import LangGraphRAG
from src.pharmaviyum.ai.mortarium_rag.vector_store import PgVectorStore


class _FakeSession:
    def __init__(self):
        self.statement = None
        self.params = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def execute(self, statement, params):
        self.statement = statement
        self.params = params
        return []


@pytest.mark.asyncio
async def test_bm25_search_builds_valid_select_sql():
    session = _FakeSession()
    store = PgVectorStore(session_factory=lambda: session)

    results = await store.bm25_search(
        "amoxicillin",
        filters={"pharmacy_id": 7, "country": "VN"},
    )

    sql = str(session.statement).lstrip()
    assert sql.startswith("SELECT")
    assert "table_name and filter keys are validated" not in sql
    assert "WHERE" in sql
    assert "AND to_tsvector('english', content)" in sql
    assert session.params["filter_0"] == 7
    assert session.params["query"] == "amoxicillin"
    assert results == []


@pytest.mark.asyncio
async def test_guardrails_node_uses_validated_output_contract():
    class _Guardrails:
        async def post_process(self, answer, question, sources):
            return SimpleNamespace(
                is_safe=True,
                validated_output="validated answer with disclaimer",
                warnings=["disclaimer_appended"],
            )

    rag = LangGraphRAG.__new__(LangGraphRAG)
    rag.guardrails = _Guardrails()

    result = await rag.guardrails_node(
        {
            "answer": "unvalidated answer",
            "question": "What does this medicine do?",
            "graded": [],
            "warnings": [],
        }
    )

    assert result["answer"] == "validated answer with disclaimer"
    assert "disclaimer_appended" in result["warnings"]
