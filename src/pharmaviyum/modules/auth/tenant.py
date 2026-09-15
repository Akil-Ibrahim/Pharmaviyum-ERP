"""Authenticated pharmacy tenant context for application boundaries."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .deps import CurrentUser, SessionDep
from .models import PharmacyMembership


@dataclass(frozen=True, slots=True)
class TenantContext:
    """Tenant identity proven to belong to the authenticated user."""

    user_id: str
    pharmacy_id: int


async def require_pharmacy_tenant(
    pharmacy_id: int,
    current_user: CurrentUser,
    session: SessionDep,
) -> TenantContext:
    """Resolve and authorize the requested pharmacy for the current user.

    The caller may select a pharmacy only when an active membership exists.
    There is deliberately no superuser bypass: tenant scope remains explicit.
    """
    membership = await session.scalar(
        select(PharmacyMembership).where(
            PharmacyMembership.user_id == current_user.id,
            PharmacyMembership.pharmacy_id == pharmacy_id,
            PharmacyMembership.is_active.is_(True),
        )
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not authorized for this pharmacy tenant",
        )

    return TenantContext(
        user_id=str(current_user.id),
        pharmacy_id=pharmacy_id,
    )
