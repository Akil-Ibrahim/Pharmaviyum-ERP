"""
API-level Dependencies (Auth, Security).
"""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status

from src.pharmaviyum.ai.config import settings

# Simple API Key authentication for demonstration.
# In production, replace with JWT/OAuth2 via fastapi.security.HTTPBearer
API_KEYS = {
    "pharmacist-key-123": "pharmacist",
    "admin-key-456": "admin",
    "system-key-789": "system",
}


async def get_current_role(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str:
    """
    Verify API key and return the user role.
    Attach this dependency to protected endpoints.
    """
    if not settings.environment == "production" and x_api_key is None:
        # Allow bypass in development for easier testing
        return "system"

    if not x_api_key or x_api_key not in API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return API_KEYS[x_api_key]


def require_role(required_roles: list[str]):
    """
    Dependency factory to enforce role-based access at the endpoint level.
    Usage: Depends(require_role(["admin", "pharmacist"]))
    """

    async def role_checker(role: str = Depends(get_current_role)):
        if role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {required_roles}",
            )
        return role

    return role_checker
