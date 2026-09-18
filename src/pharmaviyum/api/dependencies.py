"""API-level authorization dependencies.

Authentication is provided by the canonical JWT dependency. Authorization is
based on the persisted User model; no client-controlled role claim or static
API key can grant privileges.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status

from src.pharmaviyum.modules.auth.deps import get_current_active_user
from src.pharmaviyum.models.user import User

CurrentUser = Annotated[User, Depends(get_current_active_user)]


async def get_current_role(current_user: CurrentUser) -> str:
    """Return the only role currently represented by the User model."""
    if current_user.is_superuser:
        return "admin"
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No privileged role is assigned to this account",
    )


def require_role(required_roles: list[str]):
    """Dependency factory enforcing roles backed by persisted authorization."""
    if not required_roles:
        raise ValueError("required_roles must not be empty")
    unsupported = set(required_roles) - {"admin"}
    if unsupported:
        raise ValueError(
            "Unsupported roles until a persisted role model is implemented: "
            + ", ".join(sorted(unsupported))
        )

    async def role_checker(role: str = Depends(get_current_role)) -> str:
        if role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return role

    return role_checker
