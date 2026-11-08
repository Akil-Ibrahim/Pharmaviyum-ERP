"""
Tool Calling Layer — Orchestration above MCP Client.

Best practice 2026:
- Parallel tool execution when tools are independent
- Fallback tools when primary tool fails
- Result validation against Pydantic schemas
- Circuit breaker at harness level (not just MCP)
- Tool selection based on query intent
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, cast

from pydantic import BaseModel, ValidationError

from src.pharmaviyum.ai.mcp.client import MCPClient
from src.pharmaviyum.core.logging import logger

from .structured_output import ToolCallRecord


@dataclass
class ToolSpec:
    """Specification for a tool with fallback chain."""

    name: str
    fallback_tools: list[str] = field(default_factory=list)
    timeout_seconds: float = 30.0
    result_schema: type[BaseModel] | None = None  # Optional Pydantic validation
    parallel_safe: bool = True  # Can be run in parallel with other tools?


class ToolCallingLayer:
    """
    High-level tool orchestration layer.

    Responsibilities:
    1. Execute tools with retry + fallback chains
    2. Run independent tools in parallel
    3. Validate results against schemas
    4. Record all tool calls for observability
    5. Handle circuit breaker at harness level
    """

    def __init__(
        self,
        mcp_client: MCPClient,
        tool_specs: dict[str, ToolSpec] | None = None,
    ):
        self.mcp_client = mcp_client
        self.tool_specs = tool_specs or self._default_tool_specs()

        # Circuit breaker: tool_name -> {"failures": int, "last_failure": float}
        self._circuit_breaker: dict[str, dict] = {}
        self._cb_threshold = 5
        self._cb_timeout = 60.0

    def _default_tool_specs(self) -> dict[str, ToolSpec]:
        """Default tool specifications with fallbacks."""
        return {
            "check_drug_interactions": ToolSpec(
                name="check_drug_interactions",
                fallback_tools=[],  # No fallback for safety-critical tools
                timeout_seconds=10.0,
                parallel_safe=True,
            ),
            "get_patient_history": ToolSpec(
                name="get_patient_history",
                fallback_tools=[],
                timeout_seconds=15.0,
                parallel_safe=True,
            ),
            "check_halal_compliance": ToolSpec(
                name="check_halal_compliance",
                fallback_tools=[],
                timeout_seconds=10.0,
                parallel_safe=True,
            ),
            "verify_prescription": ToolSpec(
                name="verify_prescription",
                fallback_tools=[],
                timeout_seconds=15.0,
                parallel_safe=True,
            ),
        }

    async def execute_tools(
        self,
        tool_calls: list[dict[str, Any]],
        trace_id: str | None = None,
    ) -> list[ToolCallRecord]:
        """
        Execute multiple tool calls with parallel execution where safe.

        Args:
            tool_calls: List of {"name": str, "args": dict, "id": str}
            trace_id: For observability correlation

        Returns:
            List of ToolCallRecord with results
        """
        if not tool_calls:
            return []

        # Separate parallel-safe and sequential tools
        parallel_tools = []
        sequential_tools = []

        for tc in tool_calls:
            spec = self.tool_specs.get(tc["name"])
            if spec and spec.parallel_safe:
                parallel_tools.append(tc)
            else:
                sequential_tools.append(tc)

        results: list[ToolCallRecord] = []

        # Execute parallel tools concurrently
        if parallel_tools:
            logger.debug(f"Executing {len(parallel_tools)} tools in parallel")
            parallel_results = await asyncio.gather(
                *[self._execute_single_tool(tc, trace_id) for tc in parallel_tools],
                return_exceptions=True,
            )

            for i, result in enumerate(parallel_results):
                if isinstance(result, asyncio.CancelledError):
                    raise result
                if isinstance(result, Exception):
                    logger.error(
                        "Parallel MCP tool execution failed",
                        extra={"error_type": type(result).__name__},
                    )
                    results.append(
                        ToolCallRecord(
                            tool_name=parallel_tools[i]["name"],
                            input_data=parallel_tools[i].get("args", {}),
                            success=False,
                            error="Tool execution failed",
                        )
                    )
                else:
                    results.append(cast(ToolCallRecord, result))

        # Execute sequential tools one by one
        for tc in sequential_tools:
            result = await self._execute_single_tool(tc, trace_id)
            results.append(result)

        return results

    async def _execute_single_tool(
        self,
        tool_call: dict[str, Any],
        trace_id: str | None = None,
    ) -> ToolCallRecord:
        """Execute a single tool with fallback chain and validation."""
        tool_name = tool_call["name"]
        tool_args = tool_call.get("args", {})
        spec = self.tool_specs.get(tool_name)

        # Check circuit breaker
        if self._is_circuit_open(tool_name):
            logger.warning("MCP tool circuit breaker is open")
            return ToolCallRecord(
                tool_name=tool_name,
                input_data=tool_args,
                success=False,
                error="Circuit breaker open",
                latency_ms=0.0,
            )

        # Try primary tool, then fallbacks
        tools_to_try = [tool_name] + (spec.fallback_tools if spec else [])
        total_latency = 0.0

        for attempt_tool in tools_to_try:
            start = time.perf_counter()

            try:
                result = await self.mcp_client.call_tool(
                    tool_name=attempt_tool,
                    input_data=tool_args,
                    trace_id=trace_id,
                )
                latency_ms = (time.perf_counter() - start) * 1000
                total_latency += latency_ms

                if result.success:
                    # Validate result schema if specified
                    if spec and spec.result_schema:
                        try:
                            spec.result_schema.model_validate(result.data)
                        except ValidationError as e:
                            logger.warning(
                                "MCP tool result validation failed",
                                extra={"error_type": type(e).__name__},
                            )
                            continue

                    # Reset circuit breaker on success
                    if tool_name in self._circuit_breaker:
                        del self._circuit_breaker[tool_name]

                    return ToolCallRecord(
                        tool_name=attempt_tool,
                        input_data=tool_args,
                        success=True,
                        output_summary=self._summarize_output(result.data),
                        latency_ms=latency_ms,
                    )
                else:
                    logger.warning(
                        "MCP tool returned an unsuccessful result",
                        extra={},
                    )

            except Exception as exc:
                latency_ms = (time.perf_counter() - start) * 1000
                total_latency += latency_ms
                logger.error(
                    "MCP tool execution raised an exception",
                    extra={"error_type": type(exc).__name__},
                )

        # All tools in fallback chain failed
        self._record_failure(tool_name)

        return ToolCallRecord(
            tool_name=tool_name,
            input_data=tool_args,
            success=False,
            error="All configured tool attempts failed.",
            latency_ms=total_latency,
        )

    def _summarize_output(self, data: Any) -> str:
        """Create a brief summary of tool output for LLM context."""
        if isinstance(data, dict):
            # Extract key fields for summary
            summary_parts = []
            for key in [
                "status",
                "severity",
                "is_valid",
                "is_halal",
                "overall_severity",
            ]:
                if key in data:
                    summary_parts.append(f"{key}={data[key]}")
            return ", ".join(summary_parts) if summary_parts else str(data)[:200]
        return str(data)[:200]

    def _is_circuit_open(self, tool_name: str) -> bool:
        """Check if circuit breaker is open for tool."""
        if tool_name not in self._circuit_breaker:
            return False

        cb = self._circuit_breaker[tool_name]
        if cb["failures"] < self._cb_threshold:
            return False

        # Check if timeout elapsed (half-open state)
        if time.time() - cb["last_failure"] > self._cb_timeout:
            del self._circuit_breaker[tool_name]
            return False

        return True

    def _record_failure(self, tool_name: str):
        """Record tool failure for circuit breaker."""
        if tool_name not in self._circuit_breaker:
            self._circuit_breaker[tool_name] = {"failures": 0, "last_failure": 0.0}

        self._circuit_breaker[tool_name]["failures"] += 1
        self._circuit_breaker[tool_name]["last_failure"] = time.time()
