"""Request logging middleware.

Logs basic request information (method, path, duration, and status) using the
application's standard logger.
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.pharmaviyum.core.logging import get_logger

logger = get_logger("pharmaviyum.middleware")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Simple timing and request logging middleware."""

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        start = time.monotonic()
        response = await call_next(request)
        duration = (time.monotonic() - start) * 1000
        logger.info(
            "http_request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round(duration, 2),
            },
        )
        return response


def add_logging_middleware(app: ASGIApp) -> None:
    """Register request logging middleware on the application."""
    app.add_middleware(LoggingMiddleware)


__all__ = ["add_logging_middleware", "LoggingMiddleware"]
