"""Regression tests for Mortarium RAG and model-router agent integration."""

import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import ValidationError

from src.pharmaviyum.ai.agents.pharmacist_agent import PharmacistAgent
from src.pharmaviyum.ai.mortarium_rag.graph import LangGraphRAG
from src.pharmaviyum.ai.mortarium_rag.schemas import QueryContext


def test_rag_filters_omit_unknown_optional_country() -> None:
    context = QueryContext(user_id="user-1", pharmacy_id=7, country=None)

    assert LangGraphRAG._build_filters(context) == {
        "pharmacy_id": 7,
        "_search_language": "en",
    }


def test_rag_filters_keep_known_country_and_halal_constraint() -> None:
    context = QueryContext(
        user_id="user-1",
        pharmacy_id=7,
        country="VN",
        halal_filter=True,
    )

    assert LangGraphRAG._build_filters(context) == {
        "pharmacy_id": 7,
        "_search_language": "en",
        "country": "VN",
        "halal": True,
    }


@pytest.mark.asyncio
async def test_knowledge_retrieval_node_calls_tenant_scoped_rag() -> None:
    chunk = SimpleNamespace(
        id="chunk-123",
        document_id="document-456",
        content="Paracetamol is an analgesic.",
        metadata={"source": "formulary.pdf", "version": "2026.1"},
    )
    rag = AsyncMock()
    rag.run.return_value = SimpleNamespace(
        answer="Paracetamol is an analgesic [src-chunk-123].",
        citations=[],
        sources=[SimpleNamespace(chunk=chunk, score=0.91, rerank_score=None)],
        warnings=[],
    )
    agent = PharmacistAgent.__new__(PharmacistAgent)
    agent.rag_pipeline = rag

    result = await agent.knowledge_retrieval_node(
        {
            "messages": [HumanMessage(content="What is paracetamol?")],
            "context": {
                "user_id": "user-1",
                "pharmacy_id": 7,
                "patient_id": 12,
                "country": "VN",
                "language": "en",
                "halal_filter": False,
                "force_fresh": True,
                "session_id": "session-1",
            },
        }
    )

    rag.run.assert_awaited_once()
    call = rag.run.await_args.kwargs
    assert call["question"] == "What is paracetamol?"
    assert call["context"].pharmacy_id == 7
    assert call["context"].patient_id == 12
    assert call["context"].country == "VN"
    assert call["thread_id"] == "session-1"
    assert result["rag_sources"][0]["source_id"] == "src-chunk-123"
    assert json.loads(result["rag_context"])["answer"].startswith("Paracetamol")


@pytest.mark.asyncio
async def test_planner_uses_model_selected_by_router() -> None:
    agent = PharmacistAgent.__new__(PharmacistAgent)
    agent.main_llm = MagicMock()
    agent.mcp_client = MagicMock()
    agent.mcp_client.to_openai_tools.return_value = []
    selected_model = MagicMock()
    selected_model.bind_tools.return_value.ainvoke = AsyncMock(
        return_value=AIMessage(content="Grounded answer")
    )

    result = await agent.planner_node(
        {
            "messages": [HumanMessage(content="What is this medicine?")],
            "context": {"country": "VN", "language": "en"},
            "rag_context": "{}",
        },
        config={"configurable": {"selected_model": selected_model}},
    )

    selected_model.bind_tools.assert_called_once_with([])
    agent.main_llm.bind_tools.assert_not_called()
    assert result["messages"][0].content == "Grounded answer"


def test_harness_accepts_only_citations_from_retrieved_rag_sources() -> None:
    from src.pharmaviyum.ai.harness.agent_harness import AgentHarness

    source_id = "src-chunk-123"
    source = {"source_id": source_id}
    answer, warnings = AgentHarness._validate_rag_citations(
        f"Evidence-backed answer [{source_id}].", [source]
    )

    assert answer == f"Evidence-backed answer [{source_id}]."
    assert warnings == []


def test_harness_blocks_missing_or_fabricated_rag_citations() -> None:
    from src.pharmaviyum.ai.harness.agent_harness import AgentHarness

    answer, warnings = AgentHarness._validate_rag_citations(
        "Unsupported answer [src-not-retrieved].",
        [{"source_id": "src-chunk-123"}],
    )

    assert "does not preserve verifiable citations" in answer
    assert warnings == ["citation_validation_failed"]


@pytest.mark.asyncio
async def test_streaming_harness_records_phi_safe_execution_span(monkeypatch) -> None:
    import src.pharmaviyum.ai.harness.agent_harness as harness_module
    from src.pharmaviyum.ai.harness.agent_harness import AgentHarness

    span = MagicMock()
    tracer = MagicMock()
    tracer.start_span.return_value = span
    monkeypatch.setattr(harness_module, "tracer", tracer)
    harness = AgentHarness.__new__(AgentHarness)

    async def events(*args, **kwargs):
        yield {
            "event": "answer",
            "sources": [{"source_id": "src-1"}],
            "model_used": "test-model",
            "tool_result_count": 2,
        }
        yield {"event": "complete", "message": "Response ready"}

    harness._astream_events = events
    streamed = [event async for event in harness.astream("session", "sensitive query")]

    assert [event["event"] for event in streamed] == ["answer", "complete"]
    span.set_attribute.assert_any_call("ai.model_name", "test-model")
    span.set_attribute.assert_any_call("ai.rag.source_count", 1)
    span.set_attribute.assert_any_call("ai.tool_result_count", 2)
    span.set_attribute.assert_any_call("ai.execution_success", True)
    attribute_names = {call.args[0] for call in span.set_attribute.call_args_list}
    assert attribute_names.isdisjoint(
        {"ai.prompt", "ai.query", "user.id", "patient.id"}
    )
    span.end.assert_called_once()


@pytest.mark.asyncio
async def test_streaming_harness_marks_error_span(monkeypatch) -> None:
    import src.pharmaviyum.ai.harness.agent_harness as harness_module
    from src.pharmaviyum.ai.harness.agent_harness import AgentHarness

    span = MagicMock()
    tracer = MagicMock()
    tracer.start_span.return_value = span
    monkeypatch.setattr(harness_module, "tracer", tracer)
    harness = AgentHarness.__new__(AgentHarness)

    async def events(*args, **kwargs):
        yield {"event": "error", "message": "safe error"}

    harness._astream_events = events
    streamed = [event async for event in harness.astream("session", "sensitive query")]

    assert streamed[0]["event"] == "error"
    span.set_attribute.assert_any_call("ai.execution_success", False)
    span.set_status.assert_called_once()
    span.end.assert_called_once()


@pytest.mark.asyncio
async def test_cached_stream_emits_complete_event() -> None:
    from types import SimpleNamespace

    from src.pharmaviyum.ai.harness.agent_harness import AgentHarness

    harness = AgentHarness.__new__(AgentHarness)
    harness.memory = SimpleNamespace(load=AsyncMock(return_value=[]))
    harness.guardrails = SimpleNamespace(
        pre_process=AsyncMock(
            return_value=SimpleNamespace(is_safe=True, sanitized_input="safe query")
        )
    )
    harness.cache = SimpleNamespace(
        get=AsyncMock(
            return_value={
                "answer": "Cached response",
                "rag_sources": [],
                "model_used": "cached-model",
            }
        )
    )

    events = [
        event async for event in harness._astream_events("session", "original query")
    ]

    assert events[-2]["event"] == "answer"
    assert events[-2]["cache_hit"] is True
    assert events[-1]["event"] == "complete"


@pytest.mark.asyncio
async def test_streaming_harness_marks_consumer_cancellation(monkeypatch) -> None:
    import src.pharmaviyum.ai.harness.agent_harness as harness_module
    from src.pharmaviyum.ai.harness.agent_harness import AgentHarness

    span = MagicMock()
    tracer = MagicMock()
    tracer.start_span.return_value = span
    monkeypatch.setattr(harness_module, "tracer", tracer)
    harness = AgentHarness.__new__(AgentHarness)

    async def events(*args, **kwargs):
        yield {
            "event": "answer",
            "sources": [],
            "model_used": "test-model",
            "tool_result_count": 0,
        }
        yield {"event": "complete", "message": "Should not be consumed"}

    harness._astream_events = events
    stream = harness.astream("session", "sensitive query")
    first_event = await stream.__anext__()
    assert first_event["event"] == "answer"
    await stream.aclose()

    span.set_attribute.assert_any_call("ai.execution_success", False)
    span.set_attribute.assert_any_call("ai.stream.cancelled", True)
    span.end.assert_called_once()


def test_agent_checkpoint_thread_id_is_opaque_and_tenant_scoped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.pharmaviyum.core.config import settings as app_settings

    monkeypatch.setattr(app_settings, "SECRET_KEY", "agent-checkpoint-test-secret")
    first = PharmacistAgent._thread_id(
        "conversation-123", {"pharmacy_id": 7, "user_id": "user-1"}
    )
    same_scope = PharmacistAgent._thread_id(
        "conversation-123", {"pharmacy_id": 7, "user_id": "user-1"}
    )
    other_user = PharmacistAgent._thread_id(
        "conversation-123", {"pharmacy_id": 7, "user_id": "user-2"}
    )
    other_pharmacy = PharmacistAgent._thread_id(
        "conversation-123", {"pharmacy_id": 8, "user_id": "user-1"}
    )

    assert first == same_scope
    assert first != other_user
    assert first != other_pharmacy
    assert first.startswith("agent:v2:")
    assert "user-1" not in first
    assert "conversation-123" not in first
    assert ":7:" not in first


def test_agent_checkpoint_thread_id_uses_unambiguous_scope_encoding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.pharmaviyum.core.config import settings as app_settings

    monkeypatch.setattr(app_settings, "SECRET_KEY", "agent-checkpoint-test-secret")
    first = PharmacistAgent._thread_id(
        "c:d", {"pharmacy_id": 7, "user_id": "a:b"}
    )
    second = PharmacistAgent._thread_id(
        "b:c:d", {"pharmacy_id": 7, "user_id": "a"}
    )

    assert first != second


@pytest.mark.parametrize(
    ("thread_id", "context"),
    [
        ("   ", {"pharmacy_id": 7, "user_id": "user-1"}),
        ("x" * 129, {"pharmacy_id": 7, "user_id": "user-1"}),
        ("session", {"pharmacy_id": 0, "user_id": "user-1"}),
        ("session", {"pharmacy_id": True, "user_id": "user-1"}),
        ("session", {"pharmacy_id": 7.5, "user_id": "user-1"}),
        ("session", {"pharmacy_id": 7, "user_id": "   "}),
        ("session", {"pharmacy_id": 7, "user_id": True}),
        ("session", {"pharmacy_id": None, "user_id": "user-1"}),
        (123, {"pharmacy_id": 7, "user_id": "user-1"}),
    ],
)
def test_agent_checkpoint_thread_id_rejects_invalid_scope(
    thread_id: Any,
    context: dict[str, Any],
) -> None:
    with pytest.raises(ValueError):
        PharmacistAgent._thread_id(thread_id, context)


def test_agent_checkpoint_thread_id_changes_when_secret_rotates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.pharmaviyum.core.config import settings as app_settings

    context = {"pharmacy_id": 7, "user_id": "user-1"}
    monkeypatch.setattr(app_settings, "SECRET_KEY", "first-agent-secret")
    first = PharmacistAgent._thread_id("conversation-123", context)
    monkeypatch.setattr(app_settings, "SECRET_KEY", "rotated-agent-secret")
    second = PharmacistAgent._thread_id("conversation-123", context)

    assert first != second


def test_agent_checkpoint_thread_id_fails_closed_without_production_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.pharmaviyum.core.config import Environment, settings as app_settings

    monkeypatch.setattr(app_settings, "SECRET_KEY", None)
    monkeypatch.setattr(app_settings, "ENVIRONMENT", Environment.PRODUCTION)

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        PharmacistAgent._thread_id(
            "conversation-123", {"pharmacy_id": 7, "user_id": "user-1"}
        )


def test_agent_checkpoint_accepts_authenticated_integer_user_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.pharmaviyum.core.config import settings as app_settings

    monkeypatch.setattr(app_settings, "SECRET_KEY", "agent-checkpoint-test-secret")
    checkpoint_id = PharmacistAgent._thread_id(
        "conversation-123", {"pharmacy_id": 7, "user_id": 42}
    )

    assert checkpoint_id.startswith("agent:v2:")
    assert len(checkpoint_id.rsplit(":", maxsplit=1)[-1]) == 64


@pytest.mark.parametrize(
    "payload",
    [
        {"pharmacy_id": True},
        {"pharmacy_id": "7"},
        {"pharmacy_id": 7, "patient_id": True},
        {"pharmacy_id": 7, "patient_id": "12"},
    ],
)
def test_ai_query_request_rejects_coerced_tenant_ids(payload) -> None:
    from src.pharmaviyum.api.v1.ai import QueryRequest

    with pytest.raises(ValidationError):
        QueryRequest(query="What is this medicine?", **payload)
