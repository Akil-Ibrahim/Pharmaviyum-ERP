"""
Metrics collection middleware
Best practice 2026: Automatic HTTP metrics collection
"""

import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.pharmaviyum.ai.observability.metrics import (
    HTTP_REQUEST_DURATION,
    HTTP_REQUESTS_IN_FLIGHT,
    HTTP_REQUESTS_TOTAL,
)
from src.pharmaviyum.core.logging import get_logger

logger = get_logger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic HTTP metrics collection

    Collects:
    - Request count by method/endpoint/status
    - Request duration histogram
    - In-progress requests gauge
    """

    # Endpoints to exclude from metrics
    EXCLUDED_PATHS = {
        "/health",
        "/ready",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and collect metrics"""
        # Skip metrics for excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        method = request.method
        endpoint = self._normalize_endpoint(request.url.path)

        # Track in-progress requests
        HTTP_REQUESTS_IN_FLIGHT.inc()

        start_time = time.time()
        try:
            response = await call_next(request)

            duration = time.time() - start_time
            status = response.status_code
            status_class = f"{status // 100}xx"
            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                route=endpoint,
                status_class=status_class,
            ).inc()
            HTTP_REQUEST_DURATION.labels(
                method=method,
                route=endpoint,
                status_class=status_class,
            ).observe(duration)

            return response

        except Exception:
            duration = time.time() - start_time

            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                route=endpoint,
                status_class="5xx",
            ).inc()
            HTTP_REQUEST_DURATION.labels(
                method=method,
                route=endpoint,
                status_class="5xx",
            ).observe(duration)

            raise

        finally:
            HTTP_REQUESTS_IN_FLIGHT.dec()

    def _normalize_endpoint(self, path: str) -> str:
        """
        Normalize endpoint path for metrics labels

        Converts:
        - /api/v1/patients/123 → /api/v1/patients/{id}
        - /api/v1/orders/abc-def → /api/v1/orders/{id}

        This prevents metrics explosion from unique IDs.
        """
        parts = path.split("/")
        normalized = []

        for i, part in enumerate(parts):
            # Skip numeric IDs
            if part.isdigit():
                normalized.append("{id}")
            # Skip UUIDs
            elif len(part) == 36 and part.count("-") == 4:
                normalized.append("{id}")
            # Skip long alphanumeric strings (likely IDs)
            elif len(part) > 20 and part.isalnum():
                normalized.append("{id}")
            else:
                normalized.append(part)

        return "/".join(normalized)
