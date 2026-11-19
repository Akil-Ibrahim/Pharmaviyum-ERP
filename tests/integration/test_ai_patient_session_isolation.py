"""Integration coverage for patient-scoped Mortarium session boundaries.

These tests use the real PostgreSQL/Redis services configured by the integration
test suite. LLM and tool execution are replaced with a deterministic harness so
no provider calls or clinical data are involved.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.pharmaviyum.ai.dependencies import get_agent_harness
from src.pharmaviyum.ai.harness.memory import DialogueMemory
from src.pharmaviyum.api.v1.ai import _scoped_session_id
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
    monkeypatch.setattr(app_settings, "SECRET_KEY", "patient-isolation-integration-secret")
    pharmacy = Pharmacy(name="AI Isolation Test Pharmacy", code="AI-ISOLATION-TEST")
    test_db.add(pharmacy)
    await test_db.flush()

    patient_a = await patient_factory.create(
        pharmacy_id=pharmacy.id, first_name="Synthetic", last_name="Patient A"
    )
    patient_b = await patient_factory.create(
        pharmacy_id=pharmacy.id, first_name="Synthetic", last_name="Patient B"
    )

    harness = RecordingHarness()
    app.dependency_overrides[get_agent_harness] = lambda: harness
    try:
        for patient_id in (patient_a.id, patient_b.id, None):
            payload = {
                "query": "Synthetic isolation test; no clinical facts.",
                "session_id": "same-browser-session",
                "patient_id": patient_id,
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
        "sync", "stream", "sync", "stream", "sync", "stream"
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

    patient_a_messages = await memory.load(patient_a_scope)
    patient_b_messages = await memory.load(patient_b_scope)
    no_patient_messages = await memory.load(no_patient_scope)

    assert [message.content for message in patient_a_messages] == [
        "synthetic patient A prompt", "synthetic patient A answer"
    ]
    assert [message.content for message in patient_b_messages] == [
        "synthetic patient B prompt", "synthetic patient B answer"
    ]
    assert [message.content for message in no_patient_messages] == [
        "general pharmacy prompt", "general pharmacy answer"
    ]
    assert "patient B" not in " ".join(str(message.content) for message in patient_a_messages)
    assert "patient A" not in " ".join(str(message.content) for message in patient_b_messages)


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
        pharmacy_id=pharmacy_b.id, first_name="Synthetic", last_name="Foreign Patient"
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
                "pharmacy_id": pharmacy_a.id,
            },
        )
    finally:
        app.dependency_overrides.pop(get_agent_harness, None)

    assert response.status_code == 404
    assert harness.calls == []
