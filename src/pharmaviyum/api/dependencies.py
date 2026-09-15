"""API-level authentication dependencies.

The application uses the canonical JWT authentication path. Legacy API-key
roles are retained only as an explicit compatibility layer backed by
environment configuration; there are no hardcoded credentials or implicit
development bypasses.
"""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from pydantic import SecretStr

from src.pharmaviyum.ai.config import settings
from src.pharmaviyum.modules.auth.deps import get_current_user


async def get_current_role(
    current_user: dict = Depends(get_current_user),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str:
    """Return a role from the authenticated JWT user.

    The legacy X-API-Key header is accepted only when an explicitly
    configured compatibility key is present. It is never optional in a
    protected endpoint and no development-mode bypass is allowed.
    """
    role = current_user.get("role")
    if isinstance(role, str) and role:
        return role

    # The current User model has no persisted role field. Superusers map to
    # the administrative role; ordinary users must not gain a privileged role
    # merely by presenting a client-controlled claim.
    if current_user.get("is_superuser") is True:
        return "admin"

    configured_keys: dict[str, SecretStr | None] = {
        "pharmacist": getattr(settings, "pharmacist_api_key", None),
        "admin": getattr(settings, "admin_api_key", None),
        "system": getattr(settings, "system_api_key", None),
    }
    for configured_role, configured_key in configured_keys.items():
        if configured_key is not None and x_api_key == configured_key.get_secret_value():
            return configured_role

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No authorized role is assigned to this account",
    )


def require_role(required_roles: list[str]):
    """Dependency factory enforcing an explicitly configured role."""
    if not required_roles:
        raise ValueError("required_roles must not be empty")

    async def role_checker(role: str = Depends(get_current_role)) -> str:
        if role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return role

    return role_checker
