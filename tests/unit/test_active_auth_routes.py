"""Regression tests for authentication routes exposed by the active FastAPI app."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from src.pharmaviyum.main import app
from src.pharmaviyum.modules.auth.routes import login as modular_login
from src.pharmaviyum.modules.auth.schemas import NewPassword


def test_password_recovery_routes_are_registered_in_active_api() -> None:
    """The active frontend must reach recovery and reset endpoints."""
    paths = app.openapi()["paths"]

    assert "/api/v1/auth/password-recovery/{email}" in paths
    assert "post" in paths["/api/v1/auth/password-recovery/{email}"]
    assert "/api/v1/auth/reset-password/" in paths
    assert "post" in paths["/api/v1/auth/reset-password/"]


def test_modular_auth_routes_do_not_gain_a_duplicate_api_prefix() -> None:
    """Router aggregation must not publish accidental /api/v1/api/v1 paths."""
    paths = app.openapi()["paths"]

    assert not any(path.startswith("/api/v1/api/v1/auth/") for path in paths)


@pytest.mark.asyncio
async def test_password_reset_rejects_a_reused_token(monkeypatch) -> None:
    """A reset JTI already claimed in Redis cannot update the password again."""
    redis = MagicMock()
    redis.set = AsyncMock(return_value=False)
    monkeypatch.setattr(modular_login, "decode_password_reset_token", lambda _: {
        "sub": "pharmacist@example.test",
        "jti": "already-used",
        "exp": 4_102_444_800,
    })
    monkeypatch.setattr(modular_login, "get_redis", AsyncMock(return_value=redis))

    session = MagicMock()
    session.execute = AsyncMock()

    with pytest.raises(HTTPException) as error:
        await modular_login.reset_password(
            NewPassword(token="reset-token", new_password="new-password-123"),
            session,
        )

    assert error.value.status_code == 400
    assert error.value.detail == "Reset token has already been used"
    session.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_password_reset_hashes_and_persists_password_after_claim(monkeypatch) -> None:
    """A valid reset token is claimed before the password hash is changed."""
    user = SimpleNamespace(
        email="pharmacist@example.test",
        is_active=True,
        hashed_password="old-hash",
    )
    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    session = MagicMock()
    session.execute = AsyncMock(return_value=result)
    session.flush = AsyncMock()

    redis = MagicMock()
    redis.set = AsyncMock(return_value=True)
    monkeypatch.setattr(modular_login, "decode_password_reset_token", lambda _: {
        "sub": user.email,
        "jti": "fresh-token",
        "exp": 4_102_444_800,
    })
    monkeypatch.setattr(modular_login, "get_redis", AsyncMock(return_value=redis))
    monkeypatch.setattr(modular_login, "get_password_hash", lambda _: "new-hash")

    response = await modular_login.reset_password(
        NewPassword(token="reset-token", new_password="new-password-123"),
        session,
    )

    assert response.message == "Password updated successfully"
    assert user.hashed_password == "new-hash"
    redis.set.assert_awaited_once()
    assert redis.set.await_args.kwargs["nx"] is True
    session.flush.assert_awaited_once()
