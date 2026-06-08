"""Authentication middleware.

This module adds a lightweight ASGI middleware that decodes a JWT from
the `Authorization` header and attaches a `user` object (or None) to
`request.state.user`. It is intended as a simple, safe default — for
production you should replace with your full auth flow and role checks.
"""

from typing import Callable
from starlette.types import ASGIApp
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from jose import jwt
from src.pharmaviyum.config import settings


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware that validates a bearer JWT and sets `request.state.user`.

    Note: This is intentionally minimal — it only decodes the token and
    extracts the `sub` claim as username. Use your user service for
    richer user objects.
    """

    def __init__(self, app: ASGIApp, secret: str | None = None):
        super().__init__(app)
        self.secret = secret or ""

    async def dispatch(self, request: Request, call_next: Callable):
        token = None
        auth = request.headers.get("authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()

        user = None
        if token and self.secret:
            try:
                payload = jwt.decode(token, self.secret, algorithms=[settings.JWT_ALGORITHM])  # type: ignore[arg-type]
                user = {"username": payload.get("sub")}
            except Exception:
                user = None

        request.state.user = user
        response = await call_next(request)
        return response


def add_auth_middleware(app):
    """Attach the auth middleware to the FastAPI app using configured key."""
    app.add_middleware(AuthMiddleware, secret=getattr(settings, "API_SECRET_KEY", None))


__all__ = ["add_auth_middleware", "AuthMiddleware"]
