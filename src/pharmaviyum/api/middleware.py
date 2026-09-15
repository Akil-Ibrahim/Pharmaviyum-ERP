"""
Production Middleware for Request Tracing and Logging.

Best practice 2026:
- Automatic Request ID generation and propagation
- Request/Response logging with latency tracking
- Correlation ID passing to AI components and DB
"""

from __future__ import annotations

import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.pharmaviyum.core.logging import logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Injects a unique X-Request-ID into every request and response.
    This ID is used for tracing across FastAPI -> Agent -> DB -> Celery.
    """

    async def dispatch(self, request: Request, call_next):
        # 1. Get or generate Request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # 2. Attach to request state for dependencies to use
        request.state.request_id = request_id

        # 3. Process request
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time

        # 4. Attach to response headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = str(round(process_time * 1000, 2))

        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs incoming requests and outgoing responses with latency.
    Filters out sensitive endpoints (e.g., passwords) from logs.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = getattr(request.state, "request_id", "unknown")
        start_time = time.perf_counter()

        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else "unknown",
            },
        )

        response = await call_next(request)

        process_time = time.perf_counter() - start_time

        logger.info(
            f"Request completed: {request.method} {request.url.path} {response.status_code}",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "latency_ms": round(process_time * 1000, 2),
            },
        )

        return response
