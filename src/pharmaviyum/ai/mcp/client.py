"""
MCP Client — Production-ready wrapper for tool execution.

Best practice 2026:
- Automatic retry with exponential backoff
- Structured error handling with fallback
- Tool metadata for model routing (latency, cost, complexity)
- OpenAI function schema generation
- Execution tracing for LangSmith integration
- Circuit breaker pattern for failing tools
- Centralized RBAC through the MCP registry
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from src.pharmaviyum.core.logging import logger

from .registry import UserRole, registry


@dataclass
class ToolExecutionResult:
    """Result of tool execution with metadata."""

    tool_name: str
    success: bool
    data: Any = None
    error: str | None = None
    latency_ms: float = 0.0
    retry_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class MCPClient:
    """Production MCP client with retry, error handling, and tracing."""

    def __init__(
        self,
        max_retries: int = 3,
        timeout_seconds: float = 30.0,
        enable_circuit_breaker: bool = True,
    ):
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.enable_circuit_breaker = enable_circuit_breaker
        self._circuit_breaker: dict[str, dict[str, float | int]] = {}
        self._circuit_breaker_threshold = 5
        self._circuit_breaker_timeout = 60.0

    async def call_tool(
        self,
        tool_name: str,
        input_data: dict[str, Any],
        user_role: UserRole | None = None,
        trace_id: str | None = None,
    ) -> ToolExecutionResult:
        """Call an MCP tool with retry while enforcing centralized RBAC.

        ``user_role`` is intentionally required for production callers. Missing
        authorization context fails closed instead of silently becoming a
        privileged ``system`` call.
        """
        start = time.perf_counter()

        if user_role is None:
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                error="MCP authorization context is required",
                latency_ms=(time.perf_counter() - start) * 1000,
            )

        if self.enable_circuit_breaker and self._is_circuit_open(tool_name):
            logger.warning("Circuit breaker open for tool: %s", tool_name)
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                error=f"Circuit breaker open: tool {tool_name} is temporarily unavailable",
                latency_ms=(time.perf_counter() - start) * 1000,
            )

        if not registry.get_tool(tool_name):
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                error=f"Unknown tool: {tool_name}",
                latency_ms=(time.perf_counter() - start) * 1000,
            )

        retry_count = 0
        last_error: str | None = None

        for attempt in range(self.max_retries + 1):
            try:
                result = await asyncio.wait_for(
                    registry.call_tool(
                        tool_name,
                        input_data,
                        user_role=user_role,
                    ),
                    timeout=self.timeout_seconds,
                )
                latency_ms = (time.perf_counter() - start) * 1000
                logger.info(
                    "Tool %s executed successfully",
                    tool_name,
                    extra={
                        "tool": tool_name,
                        "latency_ms": latency_ms,
                        "retry_count": retry_count,
                        "trace_id": trace_id,
                        "user_role": user_role,
                    },
                )
                self._circuit_breaker.pop(tool_name, None)
                return ToolExecutionResult(
                    tool_name=tool_name,
                    success=True,
                    data=result,
                    latency_ms=latency_ms,
                    retry_count=retry_count,
                    metadata={"trace_id": trace_id, "user_role": user_role},
                )
            except asyncio.TimeoutError:
                last_error = f"Tool {tool_name} timed out after {self.timeout_seconds}s"
                logger.warning(
                    last_error,
                    extra={"tool": tool_name, "attempt": attempt + 1},
                )
            except PermissionError as exc:
                # Authorization failures are deterministic and must never retry.
                last_error = str(exc)
                logger.warning(
                    "MCP tool authorization denied",
                    extra={"tool": tool_name, "user_role": user_role},
                )
                break
            except Exception as exc:
                last_error = f"Tool {tool_name} failed: {exc}"
                logger.error(
                    last_error,
                    extra={"tool": tool_name, "attempt": attempt + 1},
                    exc_info=True,
                )

            retry_count = attempt + 1
            if attempt < self.max_retries:
                wait_time = min(2**attempt, 10.0)
                await asyncio.sleep(wait_time)

        latency_ms = (time.perf_counter() - start) * 1000
        if self.enable_circuit_breaker and last_error and "not authorized" not in last_error:
            self._record_failure(tool_name)

        return ToolExecutionResult(
            tool_name=tool_name,
            success=False,
            error=last_error,
            latency_ms=latency_ms,
            retry_count=retry_count,
            metadata={"trace_id": trace_id, "user_role": user_role},
        )

    def _is_circuit_open(self, tool_name: str) -> bool:
        if tool_name not in self._circuit_breaker:
            return False
        cb_state = self._circuit_breaker[tool_name]
        if cb_state["failures"] < self._circuit_breaker_threshold:
            return False
        if (
            time.time() - float(cb_state["last_failure"])
            > self._circuit_breaker_timeout
        ):
            del self._circuit_breaker[tool_name]
            return False
        return True

    def _record_failure(self, tool_name: str) -> None:
        state = self._circuit_breaker.setdefault(
            tool_name, {"failures": 0, "last_failure": 0.0}
        )
        state["failures"] = int(state["failures"]) + 1
        state["last_failure"] = time.time()

    def list_tools(self, user_role: UserRole | None = None) -> list[Any]:
        """Return only tools authorized for the supplied role."""
        if user_role is None:
            return []
        return registry.list_tools_for_role(user_role)

    def get_tool_metadata(self, tool_name: str) -> Any | None:
        tool_info = registry.get_tool(tool_name)
        return tool_info[0] if tool_info else None

    def to_openai_tools(self, user_role: UserRole | None = None) -> list[dict[str, Any]]:
        """Expose only tools the caller is authorized to invoke."""
        if user_role is None:
            return []
        return registry.to_openai_tools(user_role=user_role)

    def get_tools_by_category(self, category: str) -> list[Any]:
        return [tool for tool in self.list_tools() if tool.category == category]

    def get_tools_by_tags(self, tags: list[str], user_role: UserRole | None = None) -> list[Any]:
        return [
            tool
            for tool in self.list_tools(user_role)
            if any(tag in tool.tags for tag in tags)
        ]

    def reset_circuit_breaker(self, tool_name: str | None = None) -> None:
        if tool_name:
            self._circuit_breaker.pop(tool_name, None)
            logger.info("Circuit breaker reset for tool: %s", tool_name)
        else:
            self._circuit_breaker.clear()
            logger.info("All circuit breakers reset")


mcp_client = MCPClient()
