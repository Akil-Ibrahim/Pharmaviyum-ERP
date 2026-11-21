"""
Audit middleware for automatic request logging
Best practice 2026: Compliance and security auditing
"""

import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.pharmaviyum.core.logging import get_logger

logger = get_logger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware for audit logging

    Logs all requests with:
    - User ID (if authenticated)
    - Request method and path
    - Response status
    - Duration
    - IP address
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process and log the request"""
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Get user ID if available
        user_id = None
        if hasattr(request.state, "user") and request.state.user:
            user_id = request.state.user.get("id")

        # Get correlation ID
        correlation_id = getattr(request.state, "correlation_id", None)

        # Log audit entry
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code}",
            extra={
                "user_id": user_id,
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            },
        )

        return response
