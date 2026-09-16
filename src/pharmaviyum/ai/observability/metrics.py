"""
Prometheus metrics for application and AI/LLM observability.

Metrics intentionally avoid tenant IDs, user IDs, session IDs, patient IDs,
or other unbounded identifiers as labels. Those belong in traces/logs, not
Prometheus label cardinality.
"""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram, REGISTRY

# Keep one registry so /metrics exposes both standard process/runtime metrics
# and application/AI metrics. Existing imports of ai_registry remain compatible.
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

AI_AGENT_EXECUTION_DURATION = Histogram(
    "ai_agent_execution_duration_seconds",
    "Time spent executing the full agent harness pipeline",
    ["country", "language"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    registry=ai_registry,
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


def record_tool_call(tool_name: str, success: bool, latency_ms: float) -> None:
    status = "success" if success else "failure"
    TOOL_CALLS_TOTAL.labels(tool_name=tool_name, status=status).inc()
    TOOL_CALL_DURATION.labels(tool_name=tool_name).observe(latency_ms / 1000.0)


def record_rag_retrieval(
    query_type: str, latency_ms: float, success: bool = True
) -> None:
    """Record RAG retrieval latency without exposing tenant/session identifiers."""
    status = "success" if success else "failure"
    RAG_RETRIEVAL_TOTAL.labels(query_type=query_type, status=status).inc()
    RAG_RETRIEVAL_DURATION.labels(query_type=query_type).observe(latency_ms / 1000.0)


def record_llm_usage(
    model_name: str, input_tokens: int, output_tokens: int, cost_usd: float
) -> None:
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
