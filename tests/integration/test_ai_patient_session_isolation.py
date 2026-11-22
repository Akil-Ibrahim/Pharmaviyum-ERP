"""Integration coverage for patient-scoped Mortarium session boundaries.

These tests use the real PostgreSQL/Redis services configured by the integration
test suite. LLM and tool execution are replaced with a deterministic harness so
no provider calls or clinical data are involved.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

import pytest
from httpx import AsyncClient
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from src.pharmaviyum.ai.agents.checkpointer import AgentCheckpointer
from src.pharmaviyum.ai.config import settings as ai_settings
from src.pharmaviyum.ai.dependencies import get_agent_harness
from src.pharmaviyum.ai.harness.memory import DialogueMemory
from src.pharmaviyum.ai.mortarium_rag.graph import LangGraphRAG
from src.pharmaviyum.ai.mortarium_rag.schemas import QueryContext
from src.pharmaviyum.api.v1.ai import _scoped_session_id
from src.pharmaviyum.core.config import Environment
from src.pharmaviyum.core.config import settings as app_settings
from src.pharmaviyum.main import app
from src.pharmaviyum.models.pharmacy import Pharmacy
from src.pharmaviyum.modules.auth.tenant import TenantContext


class RecordingHarness:
    """Deterministic harness that records the opaque scope passed by each route."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def run(self, *, session_id: str, query: str, context: dict[str, Any]):
        self.calls.append(
            {"mode": "sync", "session_id": session_id, "context": context}
        )
        return {
            "success": True,
            "answer": "Synthetic integration-test response.",
            "tool_results": [],
            "rag_sources": [],
            "warnings": [],
            "model_used": "synthetic-test-model",
            "latency_ms": 1.0,
        }

    async def astream(
        self, *, session_id: str, query: str, context: dict[str, Any]
    ) -> AsyncIterator[dict[str, Any]]:
        self.calls.append(
            {"mode": "stream", "session_id": session_id, "context": context}
        )
        yield {"event": "complete", "message": "Synthetic integration-test response."}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sync_and_stream_routes_bind_reused_session_to_patient_scope(
    authenticated_client: AsyncClient,
    test_db: AsyncSession,
    patient_factory,
    monkeypatch: pytest.MonkeyPatch,
):
    """One client session must produce distinct scopes for A, B and no patient."""
    monkeypatch.setattr(
        app_settings, "SECRET_KEY", "patient-isolation-integration-secret"
    )
    pharmacy = Pharmacy(name="AI Isolation Test Pharmacy", code="AI-ISOLATION-TEST")
    test_db.add(pharmacy)
    await test_db.flush()

    patient_a = await patient_factory.create(
        pharmacy_id=pharmacy.id,
        first_name="Synthetic",
        last_name="Patient A",
    )
    patient_b = await patient_factory.create(
        pharmacy_id=pharmacy.id,
        first_name="Synthetic",
        last_name="Patient B",
    )

    harness = RecordingHarness()
    app.dependency_overrides[get_agent_harness] = lambda: harness
    try:
        for patient_id in (patient_a.id, patient_b.id, None):
            payload = {
                "query": "Synthetic isolation test; no clinical facts.",
                "session_id": "same-browser-session",
                "patient_id": patient_id,
                "purpose": "dispensing_review" if patient_id is not None else None,
                "pharmacy_id": pharmacy.id,
                "language": "en",
            }
            sync_response = await authenticated_client.post(
                "/api/v1/ai/query", json=payload
            )
            assert sync_response.status_code == 200, sync_response.text

            stream_response = await authenticated_client.post(
                "/api/v1/ai/query/stream", json=payload
            )
            assert stream_response.status_code == 200, stream_response.text
            assert "Synthetic integration-test response." in stream_response.text
    finally:
        app.dependency_overrides.pop(get_agent_harness, None)

    assert [call["mode"] for call in harness.calls] == [
        "sync",
        "stream",
        "sync",
        "stream",
        "sync",
        "stream",
    ]
    scopes = {
        patient_id: (
            harness.calls[position * 2]["session_id"],
            harness.calls[position * 2 + 1]["session_id"],
        )
        for position, patient_id in enumerate((patient_a.id, patient_b.id, None))
    }
    for sync_scope, stream_scope in scopes.values():
        assert sync_scope == stream_scope

    assert len({scope[0] for scope in scopes.values()}) == 3
    assert all(
        call["context"]["patient_id"] == expected_patient_id
        for call, expected_patient_id in zip(
            harness.calls,
            (patient_a.id, patient_a.id, patient_b.id, patient_b.id, None, None),
            strict=True,
        )
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_patient_scoped_redis_memory_isolated_for_reused_client_session(
    test_redis,
    monkeypatch: pytest.MonkeyPatch,
):
    """Real Redis must not return one patient's dialogue to another patient."""
    monkeypatch.setattr(app_settings, "SECRET_KEY", "patient-isolation-redis-secret")
    memory = DialogueMemory(redis_client=test_redis)
    tenant = TenantContext(user_id=42, pharmacy_id=7)
    user = type("AuthenticatedUser", (), {"id": 42})()
    client_session = "same-browser-session"

    patient_a_scope = _scoped_session_id(client_session, tenant, user, 101)
    patient_b_scope = _scoped_session_id(client_session, tenant, user, 202)
    no_patient_scope = _scoped_session_id(client_session, tenant, user, None)

    await memory.save(
        patient_a_scope,
        "synthetic patient A prompt",
        "synthetic patient A answer",
    )
    await memory.save(
        patient_b_scope,
        "synthetic patient B prompt",
        "synthetic patient B answer",
    )
    await memory.save(
        no_patient_scope,
        "general pharmacy prompt",
        "general pharmacy answer",
    )

    # Exercise every persisted memory tier, not only the recent-message list.
    memory_scopes = {
        patient_a_scope: "patient A",
        patient_b_scope: "patient B",
        no_patient_scope: "no-patient",
    }
    for scope, label in memory_scopes.items():
        prefix = memory._session_prefix(scope)
        await test_redis.set(f"{prefix}:summary", f"summary for {label}")
        await test_redis.hset(f"{prefix}:episodic", "scope-marker", label)
        await test_redis.rpush(f"{prefix}:archive", f"archived {label} turn")

    patient_a_messages = await memory.load(patient_a_scope)
    patient_b_messages = await memory.load(patient_b_scope)
    no_patient_messages = await memory.load(no_patient_scope)

    patient_a_content = " ".join(str(message.content) for message in patient_a_messages)
    patient_b_content = " ".join(str(message.content) for message in patient_b_messages)
    no_patient_content = " ".join(
        str(message.content) for message in no_patient_messages
    )
    assert "synthetic patient A prompt" in patient_a_content
    assert "synthetic patient A answer" in patient_a_content
    assert "synthetic patient B prompt" in patient_b_content
    assert "synthetic patient B answer" in patient_b_content
    assert "general pharmacy prompt" in no_patient_content
    assert "general pharmacy answer" in no_patient_content
    assert "patient B" not in patient_a_content
    assert "patient A" not in patient_b_content

    # Summary and episodic state are also patient-scoped.
    assert any("summary for patient A" in str(m.content) for m in patient_a_messages)
    assert any("summary for patient B" in str(m.content) for m in patient_b_messages)
    assert any("summary for no-patient" in str(m.content) for m in no_patient_messages)
    assert await memory.get_episodic_facts(patient_a_scope) == {
        "scope-marker": "patient A"
    }
    assert await memory.get_episodic_facts(patient_b_scope) == {
        "scope-marker": "patient B"
    }
    assert await memory.get_episodic_facts(no_patient_scope) == {
        "scope-marker": "no-patient"
    }

    # Explicit clearing must remove every tier for A without affecting B or no-patient.
    patient_a_prefix = memory._session_prefix(patient_a_scope)
    patient_b_prefix = memory._session_prefix(patient_b_scope)
    no_patient_prefix = memory._session_prefix(no_patient_scope)
    await memory.clear(patient_a_scope)
    for suffix in ("messages", "summary", "episodic", "archive"):
        assert await test_redis.exists(f"{patient_a_prefix}:{suffix}") == 0
        assert await test_redis.exists(f"{patient_b_prefix}:{suffix}") == 1
        assert await test_redis.exists(f"{no_patient_prefix}:{suffix}") == 1


@pytest.mark.integration
def test_api_session_scope_binds_tenant_user_patient_and_secret(
    monkeypatch: pytest.MonkeyPatch,
):
    """API session namespaces must vary across every security boundary."""
    monkeypatch.setattr(app_settings, "SECRET_KEY", "stable-test-secret")
    tenant = TenantContext(user_id=42, pharmacy_id=7)
    user = type("AuthenticatedUser", (), {"id": 42})()
    base = _scoped_session_id("reused-session", tenant, user, 101)

    different_patient = _scoped_session_id("reused-session", tenant, user, 202)
    no_patient = _scoped_session_id("reused-session", tenant, user, None)
    different_user = _scoped_session_id(
        "reused-session",
        TenantContext(user_id=43, pharmacy_id=7),
        type("AuthenticatedUser", (), {"id": 43})(),
        101,
    )
    different_pharmacy = _scoped_session_id(
        "reused-session",
        TenantContext(user_id=42, pharmacy_id=8),
        user,
        101,
    )

    assert (
        len({base, different_patient, no_patient, different_user, different_pharmacy})
        == 5
    )
    prefix, digest = base.split(":", maxsplit=2)[1:]
    assert prefix == "v3"
    assert len(digest) == 64
    assert all(character in "0123456789abcdef" for character in digest)
    assert "reused-session" not in base

    monkeypatch.setattr(app_settings, "SECRET_KEY", "rotated-test-secret")
    rotated = _scoped_session_id("reused-session", tenant, user, 101)
    assert rotated != base


@pytest.mark.integration
def test_api_session_scope_fails_closed_without_production_secret(
    monkeypatch: pytest.MonkeyPatch,
):
    """Production must never derive stable patient scopes from a fallback key."""
    monkeypatch.setattr(app_settings, "ENVIRONMENT", Environment.PRODUCTION)
    monkeypatch.setattr(app_settings, "SECRET_KEY", None)
    tenant = TenantContext(user_id=42, pharmacy_id=7)
    user = type("AuthenticatedUser", (), {"id": 42})()

    with pytest.raises(RuntimeError, match="SECRET_KEY is required"):
        _scoped_session_id("reused-session", tenant, user, 101)


@pytest.mark.integration
def test_rag_checkpoint_scope_fails_closed_without_production_secret(
    monkeypatch: pytest.MonkeyPatch,
):
    """RAG checkpoint namespaces must fail closed when production HMAC key is absent."""
    monkeypatch.setattr(app_settings, "ENVIRONMENT", Environment.PRODUCTION)
    monkeypatch.setattr(app_settings, "SECRET_KEY", None)
    context = QueryContext(user_id="user-1", pharmacy_id=7, patient_id=101)

    with pytest.raises(RuntimeError, match="SECRET_KEY is required"):
        LangGraphRAG._thread_id("reused-session", context)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ai_api_rejects_patient_from_another_pharmacy_before_harness(
    authenticated_client: AsyncClient,
    test_db: AsyncSession,
    patient_factory,
    monkeypatch: pytest.MonkeyPatch,
):
    """A valid patient ID from another pharmacy must not reach the AI harness."""
    monkeypatch.setattr(app_settings, "SECRET_KEY", "patient-isolation-tenant-secret")
    pharmacy_a = Pharmacy(name="AI Tenant A", code="AI-TENANT-A")
    pharmacy_b = Pharmacy(name="AI Tenant B", code="AI-TENANT-B")
    test_db.add_all([pharmacy_a, pharmacy_b])
    await test_db.flush()
    foreign_patient = await patient_factory.create(
        pharmacy_id=pharmacy_b.id,
        first_name="Synthetic",
        last_name="Foreign Patient",
    )

    harness = RecordingHarness()
    app.dependency_overrides[get_agent_harness] = lambda: harness
    try:
        response = await authenticated_client.post(
            "/api/v1/ai/query",
            json={
                "query": "Synthetic isolation test.",
                "session_id": "same-browser-session",
                "patient_id": foreign_patient.id,
                "purpose": "dispensing_review",
                "pharmacy_id": pharmacy_a.id,
            },
        )
    finally:
        app.dependency_overrides.pop(get_agent_harness, None)

    assert response.status_code == 404
    assert harness.calls == []


@pytest.mark.integration
@pytest.mark.asyncio
async def test_patient_scoped_langgraph_checkpoints_are_durable_and_separate(
    test_db: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    """Real PostgreSQL checkpoints must remain isolated across patient scopes."""
    from src.pharmaviyum.core.config import settings as core_settings

    monkeypatch.setattr(
        core_settings, "SECRET_KEY", "patient-isolation-checkpoint-secret"
    )
    # CI applies the Alembic-managed checkpoint schema to the integration
    # database before running this test. Use unique thread IDs in public rather
    # than a temporary schema: runtime verification intentionally checks the
    # canonical public schema and must remain read-only.
    base_url = ai_settings.pgvector.database_url.get_secret_value().replace(
        "postgresql+asyncpg://", "postgresql://", 1
    )
    checkpointer = AgentCheckpointer(database_url=base_url, max_size=2)
    try:
        saver = await checkpointer.initialize()

        async def record_message(state: MessagesState) -> dict[str, Any]:
            original = state["messages"][-1].content
            return {"messages": [AIMessage(content=f"persisted:{original}")]}

        workflow = StateGraph(MessagesState)
        workflow.add_node("record", record_message)
        workflow.add_edge(START, "record")
        workflow.add_edge("record", END)
        graph = workflow.compile(checkpointer=saver)

        contexts = {
            "patient_a": QueryContext(user_id="user-1", pharmacy_id=7, patient_id=101),
            "patient_b": QueryContext(user_id="user-1", pharmacy_id=7, patient_id=202),
            "no_patient": QueryContext(user_id="user-1", pharmacy_id=7),
        }
        thread_ids = {
            label: LangGraphRAG._thread_id(f"checkpoint-isolation-{uuid4()}", context)
            for label, context in contexts.items()
        }
        assert len(set(thread_ids.values())) == 3

        for label, thread_id in thread_ids.items():
            await graph.ainvoke(
                {"messages": [HumanMessage(content=f"synthetic:{label}")]},
                config={"configurable": {"thread_id": thread_id}},
            )

        snapshots = {
            label: await graph.aget_state({"configurable": {"thread_id": thread_id}})
            for label, thread_id in thread_ids.items()
        }
        for label, snapshot in snapshots.items():
            contents = [message.content for message in snapshot.values["messages"]]
            assert f"synthetic:{label}" in contents
            assert f"persisted:synthetic:{label}" in contents
            for other_label in set(contexts) - {label}:
                assert f"synthetic:{other_label}" not in contents
    finally:
        await checkpointer.close()
