"""Tenant scope regression tests."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from src.pharmaviyum.modules.auth.tenant import resolve_pharmacy_scope


def user(user_id: int = 1, *, superuser: bool = False):
    return SimpleNamespace(id=user_id, is_superuser=superuser)


def membership_result(*pharmacy_ids: int):
    result = MagicMock()
    result.scalars.return_value.all.return_value = list(pharmacy_ids)
    return result


@pytest.mark.asyncio
async def test_explicit_pharmacy_requires_active_membership():
    session = SimpleNamespace(
        scalar=AsyncMock(return_value=MagicMock()),
    )

    assert await resolve_pharmacy_scope(7, user(), session) == 7
    session.scalar.assert_awaited_once()


@pytest.mark.asyncio
async def test_explicit_pharmacy_rejects_missing_membership():
    session = SimpleNamespace(
        scalar=AsyncMock(return_value=None),
    )

    with pytest.raises(HTTPException) as exc:
        await resolve_pharmacy_scope(7, user(), session)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_multiple_active_pharmacies_require_explicit_scope():
    session = SimpleNamespace(
        execute=AsyncMock(return_value=membership_result(1, 2)),
    )

    with pytest.raises(HTTPException) as exc:
        await resolve_pharmacy_scope(None, user(), session)

    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_single_active_pharmacy_is_selected_automatically():
    session = SimpleNamespace(
        execute=AsyncMock(return_value=membership_result(42)),
    )

    assert await resolve_pharmacy_scope(None, user(), session) == 42


@pytest.mark.asyncio
async def test_superuser_can_use_global_scope():
    session = SimpleNamespace(
        scalar=AsyncMock(),
        execute=AsyncMock(),
    )

    assert await resolve_pharmacy_scope(None, user(superuser=True), session) is None
    session.scalar.assert_not_awaited()
    session.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_superuser_can_select_explicit_pharmacy_without_membership():
    session = SimpleNamespace(
        scalar=AsyncMock(),
        execute=AsyncMock(),
    )

    assert await resolve_pharmacy_scope(99, user(superuser=True), session) == 99
    session.scalar.assert_not_awaited()
    session.execute.assert_not_awaited()
