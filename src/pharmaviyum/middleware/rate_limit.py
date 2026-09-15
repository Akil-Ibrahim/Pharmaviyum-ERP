"""Rate limiting middleware for production deployments."""

from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
import structlog

from src.pharmaviyum.config import settings

logger = structlog.get_logger()


def setup_rate_limiting(app: FastAPI) -> None:
    """Configure distributed rate limiting when enabled."""
    if not settings.RATE_LIMIT_ENABLED:
        logger.info("rate_limiting_disabled")
        return

    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=settings.RATE_LIMIT_STORAGE_URI,
        default_limits=[settings.RATE_LIMIT_DEFAULT],
        strategy="fixed-window",
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    logger.info(
        "rate_limiting_configured",
        default_limit=settings.RATE_LIMIT_DEFAULT,
        storage=settings.RATE_LIMIT_STORAGE_URI,
    )


def rate_limit_auth():
    """Rate limit authentication endpoints."""
    limiter = Limiter(key_func=get_remote_address)
    return limiter.limit("5/minute")


def rate_limit_api():
    """Rate limit general API endpoints."""
    limiter = Limiter(key_func=get_remote_address)
    return limiter.limit("100/minute")


def rate_limit_ai():
    """Rate limit AI endpoints."""
    limiter = Limiter(key_func=get_remote_address)
    return limiter.limit("10/minute")


def get_user_identifier(request: Request) -> str:
    """Return an authenticated user identifier, falling back to client IP."""
    user = request.scope.get("user")
    if user:
        username = user.get("username", "unknown") if isinstance(user, dict) else getattr(user, "username", "unknown")
        return f"user:{username}"
    return f"ip:{get_remote_address(request)}"
