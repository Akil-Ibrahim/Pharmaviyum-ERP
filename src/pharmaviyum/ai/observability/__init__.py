"""
Observability Module.

Public API:
- tracer: Global ObservabilityTracer instance (OpenTelemetry + LangSmith)
- ai_registry: Prometheus CollectorRegistry for AI metrics
- record_tool_call, record_llm_usage, record_evaluation_scores: Metric helpers
- calculate_llm_cost: LLM cost estimation utility
"""
from .tracer import ObservabilityTracer, tracer
from .metrics import (
    ai_registry,
    record_tool_call,
    record_llm_usage,
    record_evaluation_scores,
    AGENT_EXECUTION_DURATION,
    TOOL_CALLS_TOTAL,
    LLM_TOKENS_USED_TOTAL,
)
from .cost_tracker import calculate_llm_cost, get_model_info

__all__ = [
    "ObservabilityTracer",
    "tracer",
    "ai_registry",
    "record_tool_call",
    "record_llm_usage",
    "record_evaluation_scores",
    "AGENT_EXECUTION_DURATION",
    "TOOL_CALLS_TOTAL",
    "LLM_TOKENS_USED_TOTAL",
    "calculate_llm_cost",
    "get_model_info",
]
