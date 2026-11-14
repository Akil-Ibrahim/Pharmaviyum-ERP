from unittest.mock import AsyncMock
import pytest
from fastapi import HTTPException

from src.pharmaviyum.modules.auth.models import User
from src.pharmaviyum.modules.auth.tenant import require_pharmacy_tenant


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tenant_context_requires_active_membership():
    user = User(
        id=1,
        email="user@example.com",
        username="test-user",
        hashed_password="not-used",
        is_active=True,
        is_superuser=False,
    )
    session = AsyncMock()
    session.scalar.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await require_pharmacy_tenant(42, user, session)

    assert exc_info.value.status_code == 403
    assert "not authorized" in str(exc_info.value.detail).lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tenant_context_returns_authenticated_scope_for_active_membership():
    user = User(
        id=1,
        email="user@example.com",
        username="test-user",
        hashed_password="not-used",
        is_active=True,
        is_superuser=False,
    )
    membership = type("Membership", (), {"is_active": True})()
    session = AsyncMock()
    session.scalar.return_value = membership

    context = await require_pharmacy_tenant(42, user, session)

    assert context.user_id == user.id
    assert context.pharmacy_id == 42
