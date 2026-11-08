from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.pharmaviyum.ai.mortarium_rag.graph import LangGraphRAG
from src.pharmaviyum.ai.mortarium_rag.schemas import QueryContext


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
    context = QueryContext(user_id="user-1", pharmacy_id=7)
    assert rag._thread_id("conversation-123", context) == (
        "rag:7:user-1:conversation-123"
    )
    first = rag._thread_id(None, context)
    second = rag._thread_id(None, context)
    assert first.startswith("rag:")
    assert second.startswith("rag:")
    assert first != second
    other_tenant = QueryContext(user_id="user-1", pharmacy_id=8)
    assert rag._thread_id("conversation-123", other_tenant) != rag._thread_id(
        "conversation-123", context
    )


@pytest.mark.asyncio
async def test_no_answer_fails_closed(rag: LangGraphRAG) -> None:
    result = await rag.no_answer_node({})
    assert result["confidence"] == 0.0
    assert result["model_used"] == "none"
    assert result["tokens_used"] == 0
    assert "no_relevant_documents" in result["warnings"]
    assert "pharmacist" in result["answer"].lower()


@pytest.mark.asyncio
async def test_generate_node_accepts_gemini_text_content_blocks(
    rag: LangGraphRAG,
) -> None:
    class _LLM:
        async def ainvoke(self, prompt):
            return SimpleNamespace(
                content=[
                    {"type": "text", "text": "Check temperatures at opening"},
                    {"type": "text", "text": "and closing. [src-123]"},
                ]
            )

    rag.llm = _LLM()
    result = await rag.generate_node(
        {"question": "When are temperatures checked?", "compressed_context": ""}
    )

    assert result["answer"] == ("Check temperatures at opening\nand closing. [src-123]")


@pytest.mark.asyncio
async def test_run_reports_provider_token_usage_from_callbacks(
    rag: LangGraphRAG,
) -> None:
    class _Graph:
        async def ainvoke(self, initial, config):
            callback = config["callbacks"][0]
            callback.usage_metadata["gemini-flash"] = {
                "input_tokens": 12,
                "output_tokens": 8,
                "total_tokens": 20,
            }
            return {
                "answer": "Evidence-supported answer.",
                "graded": [],
                "confidence": 0.0,
                "model_used": "gemini-flash",
                "latency_ms": 42.0,
                "warnings": [],
            }

    rag.graph = _Graph()
    context = QueryContext(user_id="user-1", pharmacy_id=1)

    response = await rag.run("Question", context)

    assert response.tokens_used == 20


@pytest.mark.parametrize(
    "payload",
    [
        {"user_id": "", "pharmacy_id": 1},
        {"user_id": "user-1", "pharmacy_id": 0},
        {"user_id": "user-1", "pharmacy_id": -1},
        {"user_id": "user-1", "pharmacy_id": 1, "patient_id": 0},
        {"user_id": "user-1", "pharmacy_id": 1, "patient_id": -1},
    ],
)
def test_query_context_rejects_invalid_identity_and_tenant_scope(payload):
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        QueryContext(**payload)


@pytest.mark.asyncio
async def test_transform_query_always_preserves_original_query(rag: LangGraphRAG):
    class _Transformer:
        async def generate_multi_query(self, query, num_variations, context):
            return [
                SimpleNamespace(transformed_query="rewritten drug question"),
                SimpleNamespace(transformed_query=query),
                SimpleNamespace(transformed_query="unbounded third variation"),
            ]

    rag.guardrails = None
    rag.enable_multi_query = True
    rag.max_query_variations = 1
    rag.enable_hyde = False
    rag.transformer = _Transformer()

    context = QueryContext(user_id="user-1", pharmacy_id=7)
    result = await rag.transform_query_node(
        {"question": "original medicine question", "context": context}
    )

    assert result["transformed_queries"] == [
        "original medicine question",
        "rewritten drug question",
    ]


@pytest.mark.asyncio
async def test_run_sets_explicit_langgraph_recursion_limit(rag: LangGraphRAG):
    class _Graph:
        async def ainvoke(self, initial, config):
            assert config["recursion_limit"] == 18
            return {
                "answer": "No answer.",
                "graded": [],
                "confidence": 0.0,
                "model_used": "test",
                "latency_ms": 1.0,
                "warnings": [],
            }

    rag.graph = _Graph()
    rag.max_rewrites = 2
    response = await rag.run(
        "Question",
        QueryContext(user_id="user-1", pharmacy_id=1),
    )
    assert response.answer == "No answer."


@pytest.mark.asyncio
async def test_retrieval_fanout_respects_concurrency_limit(rag: LangGraphRAG):
    import asyncio

    class _Embeddings:
        async def embed(self, query):
            return [0.1, 0.2]

    class _Store:
        def __init__(self):
            self.active = 0
            self.max_active = 0

        async def hybrid_search(self, query, query_embedding, top_k, filters):
            self.active += 1
            self.max_active = max(self.max_active, self.active)
            try:
                await asyncio.sleep(0.01)
                return []
            finally:
                self.active -= 1

    store = _Store()
    rag.embeddings = _Embeddings()
    rag.vector_store = store
    rag.max_retrieval_concurrency = 2
    rag.retrieval_top_k = 5
    rag.max_context_docs = 10
    context = QueryContext(user_id="user-1", pharmacy_id=7)

    result = await rag.retrieve_node(
        {
            "question": "medicine question",
            "context": context,
            "transformed_queries": ["q1", "q2", "q3", "q4"],
        }
    )

    assert result["retrieved"] == []
    assert store.max_active == 2
    assert store.active == 0
