"""Prometheus metrics for application and AI/LLM observability."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram, REGISTRY

ai_registry = REGISTRY

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "route", "status_class"],
    registry=ai_registry,
)
HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "route", "status_class"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
    registry=ai_registry,
)
HTTP_REQUESTS_IN_FLIGHT = Gauge(
    "http_requests_in_flight",
    "Number of HTTP requests currently being processed",
    registry=ai_registry,
)

DB_POOL_SIZE = Gauge(
    "db_pool_size", "Configured PostgreSQL connection pool size", registry=ai_registry
)
DB_POOL_MAX_OVERFLOW = Gauge(
    "db_pool_max_overflow",
    "Configured PostgreSQL maximum overflow connection capacity",
    registry=ai_registry,
)
DB_POOL_CHECKED_OUT = Gauge(
    "db_pool_checked_out",
    "PostgreSQL connections currently checked out",
    registry=ai_registry,
)
DB_POOL_OVERFLOW = Gauge(
    "db_pool_overflow",
    "Current PostgreSQL pool overflow connections",
    registry=ai_registry,
)
DB_POOL_TIMEOUTS_TOTAL = Counter(
    "db_pool_timeouts_total", "PostgreSQL pool checkout timeouts", registry=ai_registry
)
DB_CONNECTION_HOLD_DURATION = Histogram(
    "db_connection_hold_duration_seconds",
    "Time a PostgreSQL connection remains checked out",
    buckets=[
        0.001,
        0.005,
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        30.0,
    ],
    registry=ai_registry,
)
DB_QUERY_TOTAL = Counter(
    "db_query_total",
    "PostgreSQL statement executions",
    ["operation", "status"],
    registry=ai_registry,
)
DB_QUERY_DURATION = Histogram(
    "db_query_duration_seconds",
    "PostgreSQL statement duration in seconds",
    ["operation"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=ai_registry,
)
DB_QUERY_ERRORS_TOTAL = Counter(
    "db_query_errors_total",
    "PostgreSQL statement failures",
    ["operation"],
    registry=ai_registry,
)

REDIS_COMMANDS_TOTAL = Counter(
    "redis_commands_total",
    "Redis command executions",
    ["operation", "status"],
    registry=ai_registry,
)
REDIS_COMMAND_DURATION = Histogram(
    "redis_command_duration_seconds",
    "Redis command duration in seconds",
    ["operation"],
    buckets=[0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    registry=ai_registry,
)
REDIS_COMMAND_ERRORS_TOTAL = Counter(
    "redis_command_errors_total",
    "Redis command failures",
    ["operation"],
    registry=ai_registry,
)
REDIS_CONNECTIONS = Gauge(
    "redis_connections", "Redis connections currently created", registry=ai_registry
)
REDIS_CONNECTIONS_AVAILABLE = Gauge(
    "redis_connections_available",
    "Redis connections currently available in the Redis pool",
    registry=ai_registry,
)
REDIS_CONNECTIONS_IN_USE = Gauge(
    "redis_connections_in_use",
    "Redis connections currently in use",
    registry=ai_registry,
)
REDIS_CONNECTION_LIMIT = Gauge(
    "redis_connection_limit",
    "Configured Redis connection pool limit",
    registry=ai_registry,
)

CELERY_TASKS_TOTAL = Counter(
    "celery_tasks_total",
    "Celery task executions",
    ["task", "queue", "status"],
    registry=ai_registry,
)
CELERY_TASK_DURATION = Histogram(
    "celery_task_duration_seconds",
    "Celery task execution duration in seconds",
    ["task", "queue"],
    buckets=[
        0.01,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        30.0,
        60.0,
        300.0,
        900.0,
        1800.0,
        3600.0,
    ],
    registry=ai_registry,
)
CELERY_TASKS_IN_FLIGHT = Gauge(
    "celery_tasks_in_flight",
    "Celery tasks currently executing",
    ["queue"],
    registry=ai_registry,
)

WORKER_TASKS_TOTAL = Counter(
    "worker_tasks_total",
    "Custom worker task executions",
    ["task", "queue", "status"],
    registry=ai_registry,
)
WORKER_TASK_DURATION = Histogram(
    "worker_task_duration_seconds",
    "Custom worker task execution duration in seconds",
    ["task", "queue"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 300.0, 900.0],
    registry=ai_registry,
)
WORKER_TASKS_IN_FLIGHT = Gauge(
    "worker_tasks_in_flight",
    "Custom worker tasks currently executing",
    ["queue"],
    registry=ai_registry,
)
WORKER_QUEUE_DEPTH = Gauge(
    "worker_queue_depth",
    "Number of queued custom worker tasks",
    ["queue"],
    registry=ai_registry,
)
WORKER_QUEUE_POLL_ERRORS_TOTAL = Counter(
    "worker_queue_poll_errors_total",
    "Custom worker queue polling failures",
    ["queue"],
    registry=ai_registry,
)
WORKER_UP = Gauge("worker_up", "Custom worker process health", registry=ai_registry)

# AI labels are deliberately bounded; locale/request attributes are not labels.
AI_AGENT_EXECUTION_DURATION = Histogram(
    "ai_agent_execution_duration_seconds",
    "Time spent executing the full agent harness pipeline",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    registry=ai_registry,
)
AI_STAGE_DURATION = Histogram(
    "ai_stage_duration_seconds",
    "AI pipeline stage duration in seconds",
    ["stage"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 300.0],
    registry=ai_registry,
)
AI_STAGE_ERRORS_TOTAL = Counter(
    "ai_stage_errors_total",
    "AI pipeline stage failures",
    ["stage"],
    registry=ai_registry,
)
AI_REQUESTS_TOTAL = Counter(
    "ai_requests_total", "AI pipeline requests", ["status"], registry=ai_registry
)
RAG_RETRIEVAL_DURATION = Histogram(
    "ai_rag_retrieval_duration_seconds",
    "Time spent in RAG vector search and reranking",
    ["query_type"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0],
    registry=ai_registry,
)
RAG_RETRIEVAL_TOTAL = Counter(
    "ai_rag_retrieval_total",
    "Total RAG retrieval attempts",
    ["query_type", "status"],
    registry=ai_registry,
)
TOOL_CALLS_TOTAL = Counter(
    "ai_tool_calls_total",
    "Total number of MCP tool calls",
    ["tool_name", "status"],
    registry=ai_registry,
)
TOOL_CALL_DURATION = Histogram(
    "ai_tool_call_duration_seconds",
    "Time spent executing individual MCP tools",
    ["tool_name"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0],
    registry=ai_registry,
)
LLM_TOKENS_USED_TOTAL = Counter(
    "ai_llm_tokens_used_total",
    "Total number of LLM tokens consumed",
    ["model_name", "token_type"],
    registry=ai_registry,
)
LLM_COST_ESTIMATE_USD_TOTAL = Counter(
    "ai_llm_cost_estimate_usd_total",
    "Estimated USD cost of LLM API usage",
    ["model_name"],
    registry=ai_registry,
)
EVALUATION_SCORES = Gauge(
    "ai_evaluation_score",
    "Latest LLM-as-a-judge evaluation scores",
    ["metric_type"],
    registry=ai_registry,
)
EVALUATION_PASS_RATE = Gauge(
    "ai_evaluation_pass_rate_percent",
    "Percentage of evaluations passing the safety/quality threshold",
    registry=ai_registry,
)

_ALLOWED_STAGES = {
    "query_transform",
    "retrieval",
    "document_grading",
    "query_rewrite",
    "context_compression",
    "generation",
    "guardrails",
    "rag_pipeline",
    "other",
}
_ALLOWED_QUERY_TYPES = {"hybrid_multi_query", "other"}
_ALLOWED_MODELS = {"qwen2.5:7b", "other"}
# Only registered production MCP tools are exposed as Prometheus labels.
# Test/dynamic tool names intentionally collapse to `other`.
_ALLOWED_TOOLS = {
    "get_patient_history",
    "check_halal_compliance",
    "check_drug_interactions",
    "verify_prescription",
    "other",
}


def _bounded(value: str, allowed: set[str], fallback: str = "other") -> str:
    return value if value in allowed else fallback


def record_ai_stage(stage: str, latency_ms: float, success: bool = True) -> None:
    stage = _bounded(stage, _ALLOWED_STAGES)
    AI_STAGE_DURATION.labels(stage=stage).observe(latency_ms / 1000.0)
    if not success:
        AI_STAGE_ERRORS_TOTAL.labels(stage=stage).inc()


def record_ai_request(success: bool) -> None:
    AI_REQUESTS_TOTAL.labels(status="success" if success else "failure").inc()


def record_tool_call(tool_name: str, success: bool, latency_ms: float) -> None:
    tool_name = _bounded(tool_name, _ALLOWED_TOOLS)
    status = "success" if success else "failure"
    TOOL_CALLS_TOTAL.labels(tool_name=tool_name, status=status).inc()
    TOOL_CALL_DURATION.labels(tool_name=tool_name).observe(latency_ms / 1000.0)


def record_rag_retrieval(
    query_type: str, latency_ms: float, success: bool = True
) -> None:
    query_type = _bounded(query_type, _ALLOWED_QUERY_TYPES)
    status = "success" if success else "failure"
    RAG_RETRIEVAL_TOTAL.labels(query_type=query_type, status=status).inc()
    RAG_RETRIEVAL_DURATION.labels(query_type=query_type).observe(latency_ms / 1000.0)


def record_llm_usage(
    model_name: str, input_tokens: int, output_tokens: int, cost_usd: float
) -> None:
    model_name = _bounded(model_name, _ALLOWED_MODELS)
    LLM_TOKENS_USED_TOTAL.labels(model_name=model_name, token_type="input").inc(
        input_tokens
    )
    LLM_TOKENS_USED_TOTAL.labels(model_name=model_name, token_type="output").inc(
        output_tokens
    )
    LLM_COST_ESTIMATE_USD_TOTAL.labels(model_name=model_name).inc(cost_usd)


def record_evaluation_scores(
    accuracy: float, safety: float, completeness: float, compliance: float
) -> None:
    EVALUATION_SCORES.labels(metric_type="accuracy").set(accuracy)
    EVALUATION_SCORES.labels(metric_type="safety").set(safety)
    EVALUATION_SCORES.labels(metric_type="completeness").set(completeness)
    EVALUATION_SCORES.labels(metric_type="compliance").set(compliance)
