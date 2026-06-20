"""
Rate Limiting Middleware
Best Practice: Always implement rate limiting in production to prevent abuse.
Use Redis for distributed rate limiting across multiple instances.
"""
from fastapi import FastAPI, Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import structlog

from src.pharmaviyum.config import settings

logger = structlog.get_logger()


def setup_rate_limiting(app: FastAPI) -> None:
    """
    Configure rate limiting for the application.
    
    Best Practices:
    - Use Redis for distributed rate limiting
    - Set different limits for different endpoints
    - Provide clear error messages
    - Log rate limit violations
    """
    if not settings.RATE_LIMIT_ENABLED:
        logger.info("rate_limiting_disabled")
        return
    
    # ✅ GOOD: Use Redis for distributed rate limiting
    # ❌ BAD: In-memory limiting (doesn't work with multiple workers)
    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=settings.RATE_LIMIT_STORAGE_URI,
        default_limits=[settings.RATE_LIMIT_DEFAULT],
        strategy="fixed-window",  # or "moving-window" for smoother limits
    )
    
    # Add SlowAPI state
    app.state.limiter = limiter
    
    # ✅ GOOD: Custom rate limit exceeded handler
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Add SlowAPI middleware
    app.add_middleware(SlowAPIMiddleware)
        logger.info(
        "rate_limiting_configured",
        default_limit=settings.RATE_LIMIT_DEFAULT,
        storage=settings.RATE_LIMIT_STORAGE_URI,
    )


# ============================================
# Rate Limit Decorators
# Best Practice: Apply different limits to different endpoints
# ============================================

def rate_limit_auth():
    """
    Rate limit for authentication endpoints.
    Stricter limits to prevent brute force attacks.
    """
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    
    limiter = Limiter(key_func=get_remote_address)
    return limiter.limit("5/minute")


def rate_limit_api():
    """
    Rate limit for general API endpoints.
    """
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    
    limiter = Limiter(key_func=get_remote_address)
    return limiter.limit("100/minute")


def rate_limit_ai():
    """
    Rate limit for AI endpoints.
    Stricter limits due to computational cost.
    """
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    
    limiter = Limiter(key_func=get_remote_address)
    return limiter.limit("10/minute")


# ============================================
# Custom Rate Limit Key Function
# Best Practice: Rate limit by user ID when authenticated# ============================================

def get_user_identifier(request: Request) -> str:
    """
    Get identifier for rate limiting.
    
    Best Practice:
    - Use user ID if authenticated
    - Fall back to IP address if not
    """
    # Check if user is authenticated
    if hasattr(request.scope, "user") and request.scope.get("user"):
        user = request.scope["user"]
        return f"user:{user.get('username', 'unknown')}"
    
    # Fall back to IP address
    return f"ip:{get_remote_address(request)}"
