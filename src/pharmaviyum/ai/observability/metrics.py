"""
Prometheus Metrics Exporter for AI/LLM Layer.

Best practice 2026:
- Standardized Prometheus metrics for AI workloads
- Tracking latency, tool success rates, token usage, and estimated costs
- Integration with FastAPI /metrics endpoint
"""
from __future__ import annotations
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry

# Custom registry to avoid conflicts with default Prometheus metrics
ai_registry = CollectorRegistry()

# ============================================================================
# LATENCY & PERFORMANCE METRICS
# ============================================================================

AGENT_EXECUTION_DURATION = Histogram(
    "ai_agent_execution_duration_seconds",
    "Time spent executing the full agent harness pipeline",
    ["session_id", "country", "language"],
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

# ============================================================================
# TOOL CALL METRICS
# ============================================================================

TOOL_CALLS_TOTAL = Counter(
    "ai_tool_calls_total",
    "Total number of MCP tool calls",
    ["tool_name", "status"],  # status: success, failure, timeout
    registry=ai_registry,
)

TOOL_CALL_DURATION = Histogram(
    "ai_tool_call_duration_seconds",
    "Time spent executing individual MCP tools",
    ["tool_name"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0],
    registry=ai_registry,
)

# ============================================================================
# LLM USAGE & COST METRICS
# ============================================================================

LLM_TOKENS_USED_TOTAL = Counter(
    "ai_llm_tokens_used_total",
    "Total number of LLM tokens consumed",
    ["model_name", "token_type"],  # token_type: input, output
    registry=ai_registry,
)

LLM_COST_ESTIMATE_USD_TOTAL = Counter(
    "ai_llm_cost_estimate_usd_total",
    "Estimated USD cost of LLM API usage",
    ["model_name"],
    registry=ai_registry,
)

# ============================================================================
# EVALUATION METRICS
# ============================================================================

EVALUATION_SCORES = Gauge(
    "ai_evaluation_score",
    "Latest LLM-as-a-judge evaluation scores",
    ["metric_type"],  # accuracy, safety, completeness, compliance
    registry=ai_registry,
)

EVALUATION_PASS_RATE = Gauge(
    "ai_evaluation_pass_rate_percent",
    "Percentage of evaluations passing the safety/quality threshold",
    registry=ai_registry,
)


def record_tool_call(tool_name: str, success: bool, latency_ms: float):
    """Helper to record tool call metrics."""
    status = "success" if success else "failure"
    TOOL_CALLS_TOTAL.labels(tool_name=tool_name, status=status).inc()
    TOOL_CALL_DURATION.labels(tool_name=tool_name).observe(latency_ms / 1000.0)


def record_llm_usage(model_name: str, input_tokens: int, output_tokens: int, cost_usd: float):
    """Helper to record LLM token usage and estimated cost."""
    LLM_TOKENS_USED_TOTAL.labels(model_name=model_name, token_type="input").inc(input_tokens)
    LLM_TOKENS_USED_TOTAL.labels(model_name=model_name, token_type="output").inc(output_tokens)
    LLM_COST_ESTIMATE_USD_TOTAL.labels(model_name=model_name).inc(cost_usd)


def record_evaluation_scores(accuracy: float, safety: float, completeness: float, compliance: float):
    """Helper to record latest evaluation scores."""
    EVALUATION_SCORES.labels(metric_type="accuracy").set(accuracy)
    EVALUATION_SCORES.labels(metric_type="safety").set(safety)
    EVALUATION_SCORES.labels(metric_type="completeness").set(completeness)
    EVALUATION_SCORES.labels(metric_type="compliance").set(compliance)
