"""
Metrics collection middleware
Best practice 2026: Automatic HTTP metrics collection
"""

import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.pharmaviyum.core.logging import get_logger
from src.pharmaviyum.core.metrics import HTTP_REQUESTS_IN_PROGRESS, record_http_request

logger = get_logger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic HTTP metrics collection

    Collects:
    - Request count by method/endpoint/status
    - Request duration histogram
    - Request/response sizes
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
        HTTP_REQUESTS_IN_PROGRESS.labels(method=method).inc()

        start_time = time.time()
        request_size = int(request.headers.get("content-length", 0))

        try:
            response = await call_next(request)

            duration = time.time() - start_time
            status = response.status_code
            response_size = int(response.headers.get("content-length", 0))

            # Record metrics
            record_http_request(
                method=method,
                endpoint=endpoint,
                status=status,
                duration=duration,
                request_size=request_size,
                response_size=response_size,
            )

            return response

        except Exception:
            duration = time.time() - start_time

            # Record error metrics
            record_http_request(
                method=method,
                endpoint=endpoint,
                status=500,
                duration=duration,
                request_size=request_size,
            )

            raise

        finally:
            HTTP_REQUESTS_IN_PROGRESS.labels(method=method).dec()

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
