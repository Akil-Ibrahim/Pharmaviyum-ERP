"""
Observability Module.

Public API:
- tracer: Global ObservabilityTracer instance (OpenTelemetry + LangSmith)
- ai_registry: Prometheus CollectorRegistry for AI metrics
- record_tool_call, record_llm_usage, record_evaluation_scores: Metric helpers
- calculate_llm_cost: LLM cost estimation utility
"""

from .cost_tracker import calculate_llm_cost, get_model_info
from .metrics import (AGENT_EXECUTION_DURATION, LLM_TOKENS_USED_TOTAL,
                      TOOL_CALLS_TOTAL, ai_registry, record_evaluation_scores,
                      record_llm_usage, record_tool_call)
from .tracer import ObservabilityTracer, tracer

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
