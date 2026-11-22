"""Security regression tests for selected-patient MCP PHI access."""

from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from src.pharmaviyum.ai.mcp.context import (
    MCPAuthorizationContext,
    reset_mcp_context,
    set_mcp_context,
)
from src.pharmaviyum.ai.mcp.schemas import PatientHistoryRequest
from src.pharmaviyum.ai.mcp.tools.patient_history import get_patient_history


class _FakeResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class _FakeSession:
    def __init__(self, patient=None, *, fail_commit=False):
        self.patient = patient
        self.fail_commit = fail_commit
        self.added = []
        self.commit_count = 0
        self.execute_count = 0

    def add(self, value):
        self.added.append(value)

    async def execute(self, _query):
        self.execute_count += 1
        return _FakeResult(self.patient)

    async def commit(self):
        self.commit_count += 1
        if self.fail_commit:
            raise RuntimeError("audit persistence failed")


class _SessionContext:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, *_args):
        return False


class _SessionFactory:
    def __init__(self, session):
        self.session = session

    def __call__(self):
        return _SessionContext(self.session)


def _patient():
    return SimpleNamespace(
        id=101,
        full_name="Synthetic Patient",
        date_of_birth=None,
        gender=None,
        blood_type=None,
        allergies=[],
        conditions=[],
        loyalty_tier=None,
        preferred_language="en",
    )


def _request():
    return PatientHistoryRequest(
        patient_id=101,
        include_allergies=False,
        include_conditions=False,
        include_prescriptions=False,
        include_orders=False,
    )


def _context(*, patient_id=101, purpose="dispensing_review", role="pharmacist"):
    return MCPAuthorizationContext(
        user_id=7,
        pharmacy_id=42,
        user_role=role,
        selected_patient_id=patient_id,
        purpose=purpose,
        request_id="mcp-test-request-101",
    )


@pytest.mark.asyncio
async def test_patient_history_allows_only_the_selected_patient(monkeypatch):
    from src.pharmaviyum.shared.core import database

    fake_session = _FakeSession(_patient())
    monkeypatch.setattr(
        database, "async_session_factory", _SessionFactory(fake_session)
    )
    token = set_mcp_context(_context())
    try:
        result = await get_patient_history(_request())
    finally:
        reset_mcp_context(token)

    assert result.patient_id == 101
    assert fake_session.execute_count == 1
    assert fake_session.commit_count == 1
    assert len(fake_session.added) == 1
    audit = fake_session.added[0]
    assert (audit.actor_id, audit.pharmacy_id, audit.patient_id) == (7, 42, 101)
    assert (audit.action, audit.decision, audit.purpose) == (
        "mcp_read_patient_history",
        "allowed",
        "dispensing_review",
    )
    assert audit.request_id == "mcp-test-request-101"


@pytest.mark.asyncio
async def test_patient_history_denies_model_selected_patient_mismatch(monkeypatch):
    from src.pharmaviyum.shared.core import database

    fake_session = _FakeSession(_patient())
    monkeypatch.setattr(
        database, "async_session_factory", _SessionFactory(fake_session)
    )
    token = set_mcp_context(_context(patient_id=202))
    try:
        with pytest.raises(PermissionError, match="selected patient"):
            await get_patient_history(_request())
    finally:
        reset_mcp_context(token)

    assert fake_session.execute_count == 0
    assert fake_session.commit_count == 1
    audit = fake_session.added[0]
    assert (audit.patient_id, audit.decision) == (101, "denied")


@pytest.mark.asyncio
async def test_patient_history_denies_missing_purpose_and_audits_sentinel(monkeypatch):
    from src.pharmaviyum.shared.core import database

    fake_session = _FakeSession(_patient())
    monkeypatch.setattr(
        database, "async_session_factory", _SessionFactory(fake_session)
    )
    token = set_mcp_context(_context(purpose=None))
    try:
        with pytest.raises(PermissionError, match="explicit purpose"):
            await get_patient_history(_request())
    finally:
        reset_mcp_context(token)

    assert fake_session.execute_count == 0
    audit = fake_session.added[0]
    assert (audit.decision, audit.purpose) == ("denied", "unspecified")


@pytest.mark.asyncio
async def test_patient_history_denies_non_pharmacist_even_with_matching_scope(
    monkeypatch,
):
    from src.pharmaviyum.shared.core import database

    fake_session = _FakeSession(_patient())
    monkeypatch.setattr(
        database, "async_session_factory", _SessionFactory(fake_session)
    )
    token = set_mcp_context(_context(role="admin"))
    try:
        with pytest.raises(PermissionError, match="selected patient"):
            await get_patient_history(_request())
    finally:
        reset_mcp_context(token)

    assert fake_session.execute_count == 0
    assert fake_session.added[0].decision == "denied"


@pytest.mark.asyncio
async def test_patient_history_fails_closed_when_allowed_audit_cannot_commit(
    monkeypatch,
):
    from src.pharmaviyum.shared.core import database

    fake_session = _FakeSession(_patient(), fail_commit=True)
    monkeypatch.setattr(
        database, "async_session_factory", _SessionFactory(fake_session)
    )
    token = set_mcp_context(_context())
    try:
        with pytest.raises(RuntimeError, match="audit persistence failed"):
            await get_patient_history(_request())
    finally:
        reset_mcp_context(token)

    assert fake_session.added[0].decision == "allowed"


class _RegistryInput(BaseModel):
    value: str


class _RegistryOutput(BaseModel):
    selected_patient_id: int | None
    purpose: str | None


@pytest.mark.asyncio
async def test_registry_preserves_selected_patient_and_purpose_context(monkeypatch):
    from src.pharmaviyum.ai.mcp.registry import MCPToolRegistry
    from src.pharmaviyum.ai.mcp.tool_management import health_checker

    registry = MCPToolRegistry()

    @registry.tool(
        name="inspect_patient_context",
        description="Test trusted patient context propagation",
        input_schema=_RegistryInput,
        output_schema=_RegistryOutput,
        required_roles=["pharmacist"],
        execution_class="read",
    )
    async def inspect_patient_context(_data):
        from src.pharmaviyum.ai.mcp.context import require_mcp_context

        current = require_mcp_context()
        return _RegistryOutput(
            selected_patient_id=current.selected_patient_id,
            purpose=current.purpose,
        )

    async def healthy(_tool_name):
        return {"status": "healthy", "details": ""}

    monkeypatch.setattr(health_checker, "check_tool_health", healthy)
    token = set_mcp_context(_context())
    try:
        result = await registry.call_tool(
            "inspect_patient_context",
            {"value": "test"},
            user_role="pharmacist",
            user_id=7,
            pharmacy_id=42,
        )
    finally:
        reset_mcp_context(token)

    assert result.selected_patient_id == 101
    assert result.purpose == "dispensing_review"
