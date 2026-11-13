"""Authenticated pharmacy tenant context for application boundaries."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import select

from .deps import CurrentUser, SessionDep
from .models import PharmacyMembership


@dataclass(frozen=True, slots=True)
class TenantContext:
    """Tenant identity proven to belong to the authenticated user."""

    user_id: int
    pharmacy_id: int


async def require_pharmacy_tenant(
    pharmacy_id: int,
    current_user: CurrentUser,
    session: SessionDep,
) -> TenantContext:
    """Resolve and authorize the requested pharmacy for the current user."""
    if current_user.is_superuser:
        return TenantContext(user_id=current_user.id, pharmacy_id=pharmacy_id)

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
    return TenantContext(user_id=current_user.id, pharmacy_id=pharmacy_id)


async def resolve_pharmacy_scope(
    pharmacy_id: int | None,
    current_user: CurrentUser,
    session: SessionDep,
) -> int | None:
    """Resolve an explicit tenant, or a sole active membership; superusers may remain global."""
    if current_user.is_superuser:
        return pharmacy_id
    if pharmacy_id is not None:
        await require_pharmacy_tenant(pharmacy_id, current_user, session)
        return pharmacy_id
    result = await session.execute(
        select(PharmacyMembership.pharmacy_id).where(
            PharmacyMembership.user_id == current_user.id,
            PharmacyMembership.is_active.is_(True),
        )
    )
    ids = list(result.scalars().all())
    if len(ids) != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="pharmacy_id is required when the user has multiple pharmacy tenants",
        )
    return ids[0]
