"""
Prometheus metrics for observability
Best practice 2026: Comprehensive metrics for monitoring and alerting
"""

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Enum,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)

from src.pharmaviyum.core.config import settings

# ============================================================================
# HTTP METRICS
# ============================================================================

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status", "service"],
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "status"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently in progress",
    ["method"],
)

HTTP_REQUEST_SIZE = Histogram(
    "http_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint"],
    buckets=(100, 1000, 10000, 100000, 1000000),
)

HTTP_RESPONSE_SIZE = Histogram(
    "http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint"],
    buckets=(100, 1000, 10000, 100000, 1000000, 10000000),
)


# ============================================================================
# DATABASE METRICS
# ============================================================================

DB_QUERY_DURATION = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
)

DB_CONNECTIONS_ACTIVE = Gauge(
    "db_connections_active",
    "Number of active database connections",
)

DB_CONNECTIONS_IDLE = Gauge(
    "db_connections_idle",
    "Number of idle database connections",
)

DB_ERRORS_TOTAL = Counter(
    "db_errors_total",
    "Total number of database errors",
    ["error_type"],
)


# ============================================================================
# CACHE METRICS
# ============================================================================

CACHE_HITS_TOTAL = Counter(
    "cache_hits_total",
    "Total number of cache hits",
    ["cache_type"],
)

CACHE_MISSES_TOTAL = Counter(
    "cache_misses_total",
    "Total number of cache misses",
    ["cache_type"],
)

CACHE_HIT_RATIO = Gauge(
    "cache_hit_ratio",
    "Cache hit ratio (hits / total)",
    ["cache_type"],
)


# ============================================================================
# AI / RAG METRICS
# ============================================================================

AI_REQUESTS_TOTAL = Counter(
    "ai_requests_total",
    "Total number of AI requests",
    ["task_type", "model", "status"],
)

AI_REQUEST_DURATION = Histogram(
    "ai_request_duration_seconds",
    "AI request duration in seconds",
    ["task_type", "model"],
