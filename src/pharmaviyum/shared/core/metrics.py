"""
Prometheus metrics for application monitoring.
Scrape endpoint: GET /metrics (Prometheus format)
"""

import time

from fastapi import APIRouter, Request, Response
from prometheus_client import (CONTENT_TYPE_LATEST, CollectorRegistry, Counter,
                               Gauge, Histogram, generate_latest)
from starlette.middleware.base import BaseHTTPMiddleware

metrics_registry = CollectorRegistry()

# HTTP metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"],
    registry=metrics_registry,
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=metrics_registry,
)

# Business metrics
PATIENTS_TOTAL = Gauge(
    "patients_total",
    "Total number of patients",
    ["country", "loyalty_tier"],
    registry=metrics_registry,
)

PRESCRIPTIONS_TOTAL = Counter(
    "prescriptions_total",
    "Total number of prescriptions created",
    ["type", "country"],
    registry=metrics_registry,
)

ORDERS_TOTAL = Counter(
    "orders_total",
    "Total number of orders",
    ["channel", "payment_method", "country"],
    registry=metrics_registry,
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically track HTTP metrics."""

    EXCLUDED_PATHS = {"/metrics", "/health", "/ready", "/docs", "/openapi.json"}

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        method = request.method
        endpoint = self._normalize_path(request.url.path)
        start_time = time.perf_counter()
        status_code = 200

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            status_code = 500
            raise
        finally:
            duration = time.perf_counter() - start_time

            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                endpoint=endpoint,
                status=str(status_code),
            ).inc()

            HTTP_REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint,
            ).observe(duration)

    def _normalize_path(self, path: str) -> str:
        """Normalize path to avoid high-cardinality labels."""
        parts = path.split("/")
        normalized = []

        for part in parts:
            if part.isdigit():
                normalized.append("{id}")
            elif len(part) == 36 and part.count("-") == 4:
                normalized.append("{id}")
            else:
                normalized.append(part)

        return "/".join(normalized)


metrics_router = APIRouter(tags=["metrics"])


@metrics_router.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics exposition endpoint."""
    return Response(
        content=generate_latest(metrics_registry),
        media_type=CONTENT_TYPE_LATEST,
    )
