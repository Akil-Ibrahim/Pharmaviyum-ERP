"""
MCP Client — Production-ready wrapper for tool execution.

Best practice 2026:
- Automatic retry with exponential backoff
- Structured error handling with fallback
- Tool metadata for model routing
- Execution tracing
- Circuit breaker pattern
- Centralized RBAC and trusted tenant context through the MCP registry
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from src.pharmaviyum.core.logging import logger

from .context import require_mcp_context
from .registry import UserRole, registry


def get_authorization_context():
    """Backward-compatible accessor for trusted request-scoped MCP context."""
    try:
        return require_mcp_context()
    except PermissionError:
        return None


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
        user_id: int | None = None,
        pharmacy_id: int | None = None,
    ) -> ToolExecutionResult:
        """Call an MCP tool with retry while enforcing RBAC and tenant scope."""
        start = time.perf_counter()

        # The authenticated request context is the only authority for identity.
        context = get_authorization_context()
        if context is None:
            error = (
                "MCP tool not authorized: trusted tenant context is required"
                if any(value is not None for value in (user_role, user_id, pharmacy_id))
                else "MCP authorization and tenant context are required"
            )
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                error=error,
                latency_ms=(time.perf_counter() - start) * 1000,
            )
        if (
            (user_role is not None and user_role != context.user_role)
            or (user_id is not None and user_id != context.user_id)
            or (pharmacy_id is not None and pharmacy_id != context.pharmacy_id)
        ):
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                error="MCP authorization context mismatch",
                latency_ms=(time.perf_counter() - start) * 1000,
            )
        user_role = context.user_role
        user_id = context.user_id
        pharmacy_id = context.pharmacy_id

        tool_entry = registry.get_tool(tool_name)
        if not tool_entry:
            return ToolExecutionResult(
                tool_name="unknown",
                success=False,
                error="Unknown MCP tool",
                latency_ms=(time.perf_counter() - start) * 1000,
            )

        tool_metadata, _ = tool_entry
        canonical_tool_name = tool_metadata.name
        if self.enable_circuit_breaker and self._is_circuit_open(canonical_tool_name):
            logger.warning(
                "MCP tool circuit breaker is open",
                extra={"tool": canonical_tool_name},
            )
            return ToolExecutionResult(
                tool_name=canonical_tool_name,
                success=False,
                error="Tool temporarily unavailable",
                latency_ms=(time.perf_counter() - start) * 1000,
            )
        # A write may have succeeded even if the response timed out. Never
        # automatically replay a potentially non-idempotent side effect.
        max_attempts = (
            0 if tool_metadata.execution_class == "write" else self.max_retries
        )
        retry_count = 0
        last_error: str | None = None
        for attempt in range(max_attempts + 1):
            try:
                result = await asyncio.wait_for(
                    registry.call_tool(
                        tool_name,
                        input_data,
                        user_role=user_role,
                        user_id=user_id,
                        pharmacy_id=pharmacy_id,
                    ),
                    timeout=self.timeout_seconds,
                )
                latency_ms = (time.perf_counter() - start) * 1000
                logger.info(
                    "MCP tool executed successfully",
                    extra={
                        "tool": canonical_tool_name,
                        "latency_ms": latency_ms,
                        "retry_count": retry_count,
                        "trace_id": trace_id,
                        "user_role": user_role,
                    },
                )
                self._circuit_breaker.pop(tool_name, None)
                return ToolExecutionResult(
                    tool_name=canonical_tool_name,
                    success=True,
                    data=result,
                    latency_ms=latency_ms,
                    retry_count=retry_count,
                    metadata={
                        "trace_id": trace_id,
                        "user_role": user_role,
                    },
                )
            except asyncio.TimeoutError:
                last_error = "Tool execution timed out"
                logger.warning(
                    last_error,
                    extra={"tool": canonical_tool_name, "attempt": attempt + 1},
                )
            except PermissionError:
                last_error = "MCP tool not authorized"
                logger.warning(
                    "MCP tool authorization denied",
                    extra={"tool": canonical_tool_name, "user_role": user_role},
                )
                break
            except Exception as exc:
                last_error = "Tool execution failed"
                logger.error(
                    "MCP tool execution failed",
                    extra={
                        "tool": canonical_tool_name,
                        "attempt": attempt + 1,
                        "error_type": type(exc).__name__,
                    },
                )

            retry_count = attempt + 1
            if attempt < max_attempts:
                await asyncio.sleep(min(2**attempt, 10.0))

        latency_ms = (time.perf_counter() - start) * 1000
        if (
            self.enable_circuit_breaker
            and last_error
            and "not authorized" not in last_error
        ):
            self._record_failure(canonical_tool_name)

        return ToolExecutionResult(
            tool_name=canonical_tool_name,
            success=False,
            error=last_error,
            latency_ms=latency_ms,
            retry_count=retry_count,
            metadata={
                "trace_id": trace_id,
                "user_role": user_role,
            },
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

    def _authorized_role(self, requested_role: UserRole | None) -> UserRole | None:
        """Resolve tool-discovery role exclusively from trusted request context."""
        context = get_authorization_context()
        if context is None:
            return None
        if requested_role is not None and requested_role != context.user_role:
            return None
        return context.user_role

    def list_tools(self, user_role: UserRole | None = None) -> list[Any]:
        """Return tools authorized for the authenticated request role only."""
        authorized_role = self._authorized_role(user_role)
        if authorized_role is None:
            return []
        return registry.list_tools_for_role(authorized_role)

    def get_tool_metadata(self, tool_name: str) -> Any | None:
        """Return metadata only when the authenticated role may discover the tool."""
        authorized_role = self._authorized_role(None)
        if authorized_role is None:
            return None
        return next(
            (
                metadata
                for metadata in registry.list_tools_for_role(authorized_role)
                if metadata.name == tool_name
            ),
            None,
        )

    def to_openai_tools(
        self, user_role: UserRole | None = None
    ) -> list[dict[str, Any]]:
        """Expose only tools the caller is authorized to invoke."""
        authorized_role = self._authorized_role(user_role)
        if authorized_role is None:
            return []
        return registry.to_openai_tools(user_role=authorized_role)

    def get_tools_by_category(
        self, category: str, user_role: UserRole | None = None
    ) -> list[Any]:
        return [
            tool for tool in self.list_tools(user_role) if tool.category == category
        ]

    def get_tools_by_tags(
        self, tags: list[str], user_role: UserRole | None = None
    ) -> list[Any]:
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
