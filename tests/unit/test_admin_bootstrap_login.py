"""Regression tests for the configured administrator bootstrap login."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.pharmaviyum.api.v1 import auth


@pytest.mark.asyncio
async def test_existing_bootstrap_admin_login_does_not_rehash_or_write(monkeypatch):
    """A healthy admin account should authenticate without bcrypt or DB writes."""
    admin = SimpleNamespace(
        id=7,
        username="admin",
        hashed_password="existing-hash",
        is_active=True,
        is_superuser=True,
    )
    result = MagicMock()
    result.scalar_one_or_none.return_value = admin
    db = MagicMock()
    db.execute = AsyncMock(return_value=result)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    monkeypatch.setattr(auth.settings, "ADMIN_USER", "admin")
    monkeypatch.setattr(auth.settings, "ADMIN_PASSWORD", "a-secure-bootstrap-password")
    monkeypatch.setattr(auth, "_verify_password", lambda plain, hashed: True)
    monkeypatch.setattr(
        auth,
        "create_access_token",
        lambda subject: f"token-for-{subject}",
    )

    response = await auth.token(
        SimpleNamespace(
            username="admin",
            password="a-secure-bootstrap-password",
        ),
        db,
    )

    assert response == {
        "access_token": "token-for-7",
        "token_type": "bearer",
    }
    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_existing_bootstrap_admin_is_reconciled_when_hash_is_stale(monkeypatch):
    """A changed configured password is re-hashed and persisted exactly once."""
    admin = SimpleNamespace(
        id=7,
        username="admin",
        hashed_password="stale-hash",
        is_active=True,
        is_superuser=True,
    )
    result = MagicMock()
    result.scalar_one_or_none.return_value = admin
    db = MagicMock()
    db.execute = AsyncMock(return_value=result)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    monkeypatch.setattr(auth.settings, "ADMIN_USER", "admin")
    monkeypatch.setattr(auth.settings, "ADMIN_PASSWORD", "a-secure-bootstrap-password")
    monkeypatch.setattr(auth, "_verify_password", lambda plain, hashed: False)
    monkeypatch.setattr(auth.pwd_context, "hash", lambda password: "fresh-hash")
    monkeypatch.setattr(auth, "create_access_token", lambda subject: f"token-for-{subject}")

    response = await auth.token(
        SimpleNamespace(
            username="admin",
            password="a-secure-bootstrap-password",
        ),
        db,
    )

    assert response["access_token"] == "token-for-7"
    assert admin.hashed_password == "fresh-hash"
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(admin)
