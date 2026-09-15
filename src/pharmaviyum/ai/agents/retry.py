"""
Retry Mechanisms for LangGraph Nodes.

Best practice 2026:
- Wrap fragile nodes (e.g., external API calls, complex LLM parsing) with retry logic
- Use `tenacity` for declarative, configurable retry policies
- Fallback to alternative strategies on final failure
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable

from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.pharmaviyum.core.logging import logger


# Define custom exception for node-level failures
class NodeExecutionError(Exception):
    pass


def node_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
):
    """
    Decorator for LangGraph nodes to add automatic retry with exponential backoff.

    Usage:
        @node_retry(max_attempts=3)
        async def my_fragile_node(state: AgentState) -> dict:
            ...
    """

    def decorator(func: Callable):
        return retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(
                (NodeExecutionError, asyncio.TimeoutError, ConnectionError)
            ),
            before_sleep=before_sleep_log(logger, logger.WARNING),
            reraise=True,
        )(func)

    return decorator


# Example of a retryable tool execution node
@node_retry(max_attempts=3, min_wait=2.0, max_wait=8.0)
async def resilient_tool_executor_node(state: dict[str, Any]) -> dict:
    """
    Example node demonstrating resilient execution.
    If the underlying tool call fails with a transient error,
    tenacity will automatically retry with exponential backoff.
    """
    # Simulated fragile operation
    import random

    if random.random() < 0.7:  # 70% chance of transient failure for demo
        logger.warning("Simulated transient failure in tool executor")
        raise ConnectionError("Temporary network glitch")

    logger.info("Tool executor succeeded")
    return {"tool_results": [{"status": "success"}]}
