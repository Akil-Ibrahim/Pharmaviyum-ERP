"""Request logging middleware.

Logs basic request information (method, path, duration, status) using the
application logger. Keep logs structured and minimal for production.
"""

import time
from starlette.types import ASGIApp
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from src.pharmaviyum.core.logging import get_app_logger


logger = get_app_logger("pharmaviyum.middleware")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Simple timing/logging middleware for incoming HTTP requests."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()
        try:
            response = await call_next(request)
            return response
        finally:
            duration = (time.monotonic() - start) * 1000
            logger.info(
                "http_request",
                method=request.method,
                path=request.url.path,
                status=getattr(request, "state", {}).get("status_code", None),
                duration_ms=round(duration, 2),
            )


def add_logging_middleware(app: ASGIApp) -> None:
    app.add_middleware(LoggingMiddleware)


__all__ = ["add_logging_middleware", "LoggingMiddleware"]
