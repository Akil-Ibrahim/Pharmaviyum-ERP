"""
LangChain Callback Manager for LangSmith Integration.

Best practice 2026:
- Metadata-only callbacks with explicit content tracing disabled by default
- Custom callbacks for metrics collection
- Correlation with OpenTelemetry traces
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from langchain_core.callbacks import AsyncCallbackHandler, CallbackManager

from src.pharmaviyum.core.logging import logger


class PharmaviyumCallbackHandler(AsyncCallbackHandler):
    """
    Custom callback handler for Pharmaviyum AI agent.

    Integrates:
    - Operational metrics without prompt or tool-payload logging
    - Prometheus metrics (tool calls, latency)
    - OpenTelemetry spans (correlation with trace_id)
    """

    def __init__(self, session_id: str, trace_id: str, model_name: str = "other"):
        self.session_id = session_id
        self.trace_id = trace_id
        self.model_name = model_name

    async def on_llm_start(
        self, serialized: dict[str, Any], prompts: list[str], **kwargs
    ) -> None:
        """Called when LLM starts generating."""
        logger.debug(
            "LLM generation started",
            extra={
                "trace_id": self.trace_id,
                "model": serialized.get("name", "unknown"),
            },
        )

    async def on_llm_end(self, response: Any, **kwargs) -> None:
        """Called when LLM finishes generating."""
        from src.pharmaviyum.ai.observability.cost_tracker import calculate_llm_cost
        from src.pharmaviyum.ai.observability.metrics import record_llm_usage

        llm_output = getattr(response, "llm_output", None) or {}
        usage = (
            llm_output.get("token_usage")
            or llm_output.get("usage")
            or getattr(response, "usage_metadata", None)
            or {}
        )
        input_tokens = int(
            usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0
        )
        output_tokens = int(
            usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0
        )
        if input_tokens < 0 or output_tokens < 0 or not (input_tokens or output_tokens):
            return

        model_name = (
            llm_output.get("model_name")
            or llm_output.get("model")
            or kwargs.get("name")
            or self.model_name
        )
        cost = calculate_llm_cost(model_name, input_tokens, output_tokens)
        record_llm_usage(model_name, input_tokens, output_tokens, cost)

    async def on_tool_start(
        self, serialized: dict[str, Any], input_str: str, **kwargs
    ) -> None:
        """Called when a tool starts execution."""
        tool_name = serialized.get("name", "unknown")
        logger.info(
            f"Tool execution started: {tool_name}",
            extra={
                "trace_id": self.trace_id,
                "tool": tool_name,
            },
        )

    async def on_tool_end(self, output: str, **kwargs) -> None:
        """Called when a tool finishes execution."""
        tool_name = kwargs.get("name", "unknown")
        logger.info(
            f"Tool execution completed: {tool_name}",
            extra={
                "trace_id": self.trace_id,
                "tool": tool_name,
            },
        )

    async def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool raises an error."""
        tool_name = kwargs.get("name", "unknown")
        logger.error(
            "Tool execution failed",
            extra={
                "trace_id": self.trace_id,
                "tool": tool_name,
                "error_type": type(error).__name__,
            },
        )


def create_callback_manager(
    session_id: str, trace_id: str, model_name: str = "other"
) -> CallbackManager:
    """Create a callback manager with the Pharmaviyum handler configured."""
    return CallbackManager(
        [PharmaviyumCallbackHandler(session_id, trace_id, model_name)]
    )
