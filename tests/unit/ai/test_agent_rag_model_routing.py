"""Regression tests for Mortarium RAG and model-router agent integration."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage

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
    from src.pharmaviyum.ai.harness import agent_harness as harness_module
    from src.pharmaviyum.ai.harness.agent_harness import AgentHarness

    span = MagicMock()
    monkeypatch.setattr(harness_module.tracer, "start_span", MagicMock(return_value=span))
    harness = AgentHarness.__new__(AgentHarness)

    async def events(*args, **kwargs):
        yield {"event": "answer", "sources": [{"source_id": "src-1"}],
               "model_used": "test-model", "tool_result_count": 2}

    harness._astream_events = events
    streamed = [event async for event in harness.astream("session", "sensitive query")]

    assert streamed[0]["event"] == "answer"
    span.set_attribute.assert_any_call("ai.model_name", "test-model")
    span.set_attribute.assert_any_call("ai.rag.source_count", 1)
    span.set_attribute.assert_any_call("ai.tool_result_count", 2)
    span.set_attribute.assert_any_call("ai.execution_success", True)
    attribute_names = {call.args[0] for call in span.set_attribute.call_args_list}
    assert attribute_names.isdisjoint({"ai.prompt", "ai.query", "user.id", "patient.id"})
    span.end.assert_called_once()


@pytest.mark.asyncio
async def test_streaming_harness_marks_error_span(monkeypatch) -> None:
    from src.pharmaviyum.ai.harness import agent_harness as harness_module
    from src.pharmaviyum.ai.harness.agent_harness import AgentHarness

    span = MagicMock()
    monkeypatch.setattr(harness_module.tracer, "start_span", MagicMock(return_value=span))
    harness = AgentHarness.__new__(AgentHarness)

    async def events(*args, **kwargs):
        yield {"event": "error", "message": "safe error"}

    harness._astream_events = events
    streamed = [event async for event in harness.astream("session", "sensitive query")]

    assert streamed[0]["event"] == "error"
    span.set_attribute.assert_any_call("ai.execution_success", False)
    span.set_status.assert_called_once()
    span.end.assert_called_once()
