"""
Production middleware for request tracing, logging, and HTTP metrics.

Best practice:
- Automatic Request ID generation and propagation
- Request/response logging with latency tracking
- Prometheus HTTP latency/error/in-flight metrics
- Correlation ID attached to the active OpenTelemetry span
- Low-cardinality route labels using the framework route template
"""

from __future__ import annotations

import time
import uuid

from fastapi import Request
from opentelemetry import trace
from starlette.middleware.base import BaseHTTPMiddleware

from src.pharmaviyum.ai.observability.metrics import (
    HTTP_REQUEST_DURATION,
    HTTP_REQUESTS_IN_FLIGHT,
    HTTP_REQUESTS_TOTAL,
)
from src.pharmaviyum.core.logging import logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Injects a unique X-Request-ID into every request and response.
    This ID is used for tracing across FastAPI -> Agent -> DB -> Celery.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        span = trace.get_current_span()
        if span.is_recording():
            span.set_attribute("request.id", request_id)

        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = str(round(process_time * 1000, 2))
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs requests and records HTTP metrics without unbounded Prometheus labels.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = getattr(request.state, "request_id", "unknown")
        start_time = time.perf_counter()
        HTTP_REQUESTS_IN_FLIGHT.inc()

        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else "unknown",
            },
        )

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            status_code = 500
            raise
        finally:
            process_time = time.perf_counter() - start_time
            route = self._route_label(request)
            status_class = f"{status_code // 100}xx"
            HTTP_REQUESTS_TOTAL.labels(
                method=request.method,
                route=route,
                status_class=status_class,
            ).inc()
            HTTP_REQUEST_DURATION.labels(
                method=request.method,
                route=route,
                status_class=status_class,
            ).observe(process_time)
            HTTP_REQUESTS_IN_FLIGHT.dec()

            logger.info(
                f"Request completed: {request.method} {request.url.path} {status_code}",
                extra={
                    "request_id": request_id,
                    "status_code": status_code,
                    "latency_ms": round(process_time * 1000, 2),
                },
            )

        return response

    @staticmethod
    def _route_label(request: Request) -> str:
        """Return a stable route template instead of a dynamic URL path."""
        route = request.scope.get("route")
        route_path = getattr(route, "path", None)
        if route_path:
            return route_path
        return "unmatched"
