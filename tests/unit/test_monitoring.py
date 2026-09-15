"""Operational health/readiness endpoint tests."""
from __future__ import annotations

import pytest

from src.pharmaviyum.api.v1 import monitoring


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_is_liveness_only() -> None:
    result = await monitoring.health_check()
    assert result == {"status": "healthy", "service": "pharmaviyum-ai"}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_readiness_returns_503_on_dependency_failure(monkeypatch) -> None:
    async def fail_postgres() -> None:
        raise ConnectionError("database unavailable")

    async def ok_redis() -> None:
        return None

    monkeypatch.setattr(monitoring, "_check_postgres", fail_postgres)
    monkeypatch.setattr(monitoring, "_check_redis", ok_redis)
    monkeypatch.setattr(monitoring.ai_container, "_initialized", True)

    response = await monitoring.readiness_check()

    assert response.status_code == 503
    assert response.body
    assert b'"status":"not_ready"' in response.body
    assert b'"postgres":"failed"' in response.body
