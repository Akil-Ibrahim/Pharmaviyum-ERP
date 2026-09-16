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
# AI / MORTARIUM METRICS
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
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

AI_TOKENS_USED = Counter(
    "ai_tokens_used_total",
    "Total number of tokens used by AI",
    ["model", "type"],  # token type: input/output
)

AI_CONFIDENCE_SCORE = Histogram(
    "ai_confidence_score",
    "AI confidence score distribution",
    ["task_type"],
    buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)

AI_HALLUCINATIONS_TOTAL = Counter(
    "ai_hallucinations_total",
    "Total number of detected AI hallucinations",
    ["task_type"],
)

AI_CACHE_HIT_RATIO = Gauge(
    "ai_cache_hit_ratio",
    "AI response cache hit ratio",
)


# ============================================================================
# BUSINESS METRICS
# ============================================================================

PATIENTS_CREATED_TOTAL = Counter(
    "patients_created_total",
    "Total number of patients created",
    ["country"],
)

PRESCRIPTIONS_CREATED_TOTAL = Counter(
    "prescriptions_created_total",
    "Total number of prescriptions created",
    ["type"],  # regular/controlled/narcotic
)

PRESCRIPTIONS_FILLED_TOTAL = Counter(
    "prescriptions_filled_total",
    "Total number of prescription fills",
    ["pharmacy_id"],
)

ORDERS_CREATED_TOTAL = Counter(
    "orders_created_total",
    "Total number of orders created",
    ["channel", "payment_method"],  # channel: web/mobile/pos
)

REVENUE_TOTAL = Counter(
    "revenue_total",
    "Total revenue in smallest currency unit",
    ["currency", "pharmacy_id"],
)

NOTIFICATIONS_SENT_TOTAL = Counter(
    "notifications_sent_total",
    "Total number of notifications sent",
    ["channel", "status"],  # channel: zalo/line/whatsapp, status: success/failed
)


# ============================================================================
# BACKGROUND WORKER METRICS
# ============================================================================

WORKER_TASKS_TOTAL = Counter(
    "worker_tasks_total",
    "Total number of background tasks processed",
    ["task_name", "queue", "status"],  # status: success/failed
)

WORKER_TASK_DURATION = Histogram(
    "worker_task_duration_seconds",
    "Background task duration in seconds",
    ["task_name", "queue"],
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0),
)

WORKER_QUEUE_LENGTH = Gauge(
    "worker_queue_length",
    "Number of tasks in queue",
    ["queue"],
)

WORKER_DEAD_LETTER_COUNT = Gauge(
    "worker_dead_letter_count",
    "Number of tasks in dead letter queue",
)


# ============================================================================
# POS INTEGRATION METRICS
# ============================================================================

POS_SYNC_TOTAL = Counter(
    "pos_sync_total",
    "Total number of POS sync operations",
    ["pos_system", "entity_type", "status"],
)

POS_SYNC_DURATION = Histogram(
    "pos_sync_duration_seconds",
    "POS sync duration in seconds",
    ["pos_system", "entity_type"],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 300.0),
)

POS_SYNC_RECORDS = Counter(
    "pos_sync_records_total",
    "Total number of records synced from POS",
    ["pos_system", "entity_type", "operation"],  # operation: created/updated
)


# ============================================================================
# SECURITY METRICS
# ============================================================================

AUTH_ATTEMPTS_TOTAL = Counter(
    "auth_attempts_total",
    "Total number of authentication attempts",
    ["status"],  # success/failed
)

RATE_LIMIT_EXCEEDED_TOTAL = Counter(
    "rate_limit_exceeded_total",
    "Total number of rate limit violations",
    ["endpoint"],
)

SECURITY_EVENTS_TOTAL = Counter(
    "security_events_total",
    "Total number of security events",
    ["event_type"],  # xss_attempt, injection_attempt, etc
)


# ============================================================================
# SYSTEM METRICS
# ============================================================================

APP_INFO = Info(
    "app",
    "Application information",
)

APP_INFO.info(
    {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT.value,
    }
)

APP_UPTIME_SECONDS = Gauge(
    "app_uptime_seconds",
    "Application uptime in seconds",
)

APP_HEALTH_STATUS = Enum(
    "app_health_status",
    "Application health status",
    states=["healthy", "degraded", "unhealthy", "unknown"],
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_metrics() -> tuple[bytes, str]:
    """
    Get Prometheus metrics in text format

    Returns:
        Tuple of (metrics_bytes, content_type)
    """
    return generate_latest(), CONTENT_TYPE_LATEST


def record_http_request(
    method: str,
    endpoint: str,
    status: int,
    duration: float,
    request_size: int = 0,
    response_size: int = 0,
) -> None:
    """Record HTTP request metrics"""
    status_str = str(status)

    HTTP_REQUESTS_TOTAL.labels(
        method=method,
        endpoint=endpoint,
        status=status_str,
        service=settings.APP_NAME,
    ).inc()

    HTTP_REQUEST_DURATION.labels(
        method=method,
        endpoint=endpoint,
        status=status_str,
    ).observe(duration)

    if request_size > 0:
        HTTP_REQUEST_SIZE.labels(method=method, endpoint=endpoint).observe(request_size)

    if response_size > 0:
        HTTP_RESPONSE_SIZE.labels(method=method, endpoint=endpoint).observe(
            response_size
        )


def record_cache_hit(cache_type: str, hit: bool) -> None:
    """Record cache hit/miss"""
    if hit:
        CACHE_HITS_TOTAL.labels(cache_type=cache_type).inc()
    else:
        CACHE_MISSES_TOTAL.labels(cache_type=cache_type).inc()


def record_ai_request(
    task_type: str,
    model: str,
    status: str,
    duration: float,
    tokens_input: int = 0,
    tokens_output: int = 0,
    confidence: float = 0.0,
) -> None:
    """Record AI request metrics"""
    AI_REQUESTS_TOTAL.labels(
        task_type=task_type,
        model=model,
        status=status,
    ).inc()

    AI_REQUEST_DURATION.labels(
        task_type=task_type,
        model=model,
    ).observe(duration)

    if tokens_input > 0:
        AI_TOKENS_USED.labels(model=model, type="input").inc(tokens_input)

    if tokens_output > 0:
        AI_TOKENS_USED.labels(model=model, type="output").inc(tokens_output)

    if confidence > 0:
        AI_CONFIDENCE_SCORE.labels(task_type=task_type).observe(confidence)
