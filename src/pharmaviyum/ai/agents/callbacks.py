"""
LangChain Callback Manager for LangSmith Integration.

Best practice 2026:
- Automatic LangSmith tracing for all LLM calls
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
    - LangSmith tracing (automatic via environment)
    - Prometheus metrics (tool calls, latency)
    - OpenTelemetry spans (correlation with trace_id)
    """

    def __init__(self, session_id: str, trace_id: str):
        self.session_id = session_id
        self.trace_id = trace_id

    async def on_llm_start(
        self, serialized: dict[str, Any], prompts: list[str], **kwargs
    ) -> None:
        """Called when LLM starts generating."""
        logger.debug(
            "LLM generation started",
            extra={
                "session_id": self.session_id,
                "trace_id": self.trace_id,
                "model": serialized.get("name", "unknown"),
            },
        )

    async def on_llm_end(self, response: Any, **kwargs) -> None:
        """Called when LLM finishes generating."""
        token_usage = getattr(response, "llm_output", {}).get("token_usage", {})

        if token_usage:
            from src.pharmaviyum.ai.observability.cost_tracker import calculate_llm_cost
            from src.pharmaviyum.ai.observability.metrics import record_llm_usage

            model_name = "qwen2.5:7b"
            input_tokens = token_usage.get("prompt_tokens", 0)
            output_tokens = token_usage.get("completion_tokens", 0)
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
                "session_id": self.session_id,
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
                "session_id": self.session_id,
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
            f"Tool execution failed: {tool_name} - {error}",
            extra={
                "session_id": self.session_id,
                "trace_id": self.trace_id,
                "tool": tool_name,
                "error": str(error),
            },
            exc_info=True,
        )


def create_callback_manager(session_id: str, trace_id: str) -> CallbackManager:
    """Create a callback manager with the Pharmaviyum handler configured."""
    return CallbackManager([PharmaviyumCallbackHandler(session_id, trace_id)])
