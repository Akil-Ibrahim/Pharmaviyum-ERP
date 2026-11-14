"""Authorization helpers backed by the canonical authenticated User."""

from collections.abc import Callable
from functools import wraps

from fastapi import Depends, HTTPException, status

from src.pharmaviyum.models.user import User
from src.pharmaviyum.modules.auth.deps import get_current_active_user


async def get_current_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Return the canonical authenticated user from the database."""
    return current_user


async def get_current_active_user_alias(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Backward-compatible alias for routes using the legacy RBAC dependency."""
    return current_user


def require_role(minimum_role: str) -> Callable:
    """Require a privileged role without trusting a client-controlled JWT claim.

    Until a persisted role model is introduced, ``superuser`` is the only
    authoritative privileged role. Other role names fail closed.
    """
    if minimum_role not in {"admin", "manager", "pharmacist", "cashier", "superadmin"}:
        raise ValueError(f"Unknown role: {minimum_role}")

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not isinstance(current_user, User):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                )
            if not current_user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Inactive user",
                )
            if not current_user.is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires {minimum_role} role or higher",
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# Existing patient routes import this exact name. It now returns the canonical User.
get_current_active_user_legacy = get_current_active_user_alias
