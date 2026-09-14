"""
MCP Client — Production-ready wrapper for tool execution.

Best practice 2026:
- Automatic retry with exponential backoff
- Structured error handling with fallback
- Tool metadata for model routing (latency, cost, complexity)
- OpenAI function schema generation
- Execution tracing for LangSmith integration
- Circuit breaker pattern for failing tools
"""
from __future__ import annotations
import time
import asyncio
from typing import Any, Callable
from dataclasses import dataclass
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .registry import registry, ToolMetadata
from .schemas import MCPToolResponse
from src.pharmaviyum.core.logging import logger


@dataclass
class ToolExecutionResult:
    """Result of tool execution with metadata."""
    tool_name: str
    success: bool
    data: Any = None
    error: str | None = None
    latency_ms: float = 0.0
    retry_count: int = 0
    metadata: dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class MCPClient:
    """
    Production MCP client with retry, error handling, and tracing.
    
    Usage:
        client = MCPClient()
        
        # Call tool
        result = await client.call_tool(
            "check_drug_interactions",
            {"drug_names": ["Warfarin", "Aspirin"], "country": "VN"}
        )
        
        if result.success:
            interactions = result.data
        else:
            logger.error(f"Tool failed: {result.error}")
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        timeout_seconds: float = 30.0,
        enable_circuit_breaker: bool = True,
    ):
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.enable_circuit_breaker = enable_circuit_breaker
        
        # Circuit breaker state: tool_name -> {"failures": int, "last_failure": timestamp}
        self._circuit_breaker: dict[str, dict] = {}
        self._circuit_breaker_threshold = 5  # failures before opening circuit
        self._circuit_breaker_timeout = 60.0  # seconds to wait before retrying
    
    async def call_tool(
        self,
        tool_name: str,
        input_data: dict[str, Any],
        trace_id: str | None = None,
    ) -> ToolExecutionResult:
        """
        Call an MCP tool with retry and error handling.
        
        Args:
            tool_name: Name of registered tool
            input_data: Input data (will be validated against schema)
            trace_id: Optional trace ID for LangSmith integration
        
        Returns:
            ToolExecutionResult with success status and data/error
        """
        start = time.perf_counter()
        
        # Check circuit breaker
        if self.enable_circuit_breaker and self._is_circuit_open(tool_name):
            logger.warning(f"Circuit breaker open for tool: {tool_name}")
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                error=f"Circuit breaker open: tool {tool_name} is temporarily unavailable",
                latency_ms=(time.perf_counter() - start) * 1000,
            )
        
        # Get tool from registry
        tool_info = registry.get_tool(tool_name)
        if not tool_info:
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                error=f"Unknown tool: {tool_name}",
                latency_ms=(time.perf_counter() - start) * 1000,
            )
        
        metadata, func = tool_info
        
        # Execute with retry
        retry_count = 0
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Execute with timeout
                result = await asyncio.wait_for(
                    self._execute_tool(func, input_data, metadata),
                    timeout=self.timeout_seconds,
                )
                
                latency_ms = (time.perf_counter() - start) * 1000
                
                logger.info(
                    f"Tool {tool_name} executed successfully",
                    extra={
                        "tool": tool_name,
                        "latency_ms": latency_ms,
                        "retry_count": retry_count,
                        "trace_id": trace_id,
                    },
                )
                
                # Reset circuit breaker on success
                if tool_name in self._circuit_breaker:
                    del self._circuit_breaker[tool_name]
                
                return ToolExecutionResult(
                    tool_name=tool_name,
                    success=True,
                    data=result,
                    latency_ms=latency_ms,
                    retry_count=retry_count,
                    metadata={"trace_id": trace_id} if trace_id else {},
                )
            
            except asyncio.TimeoutError:
                last_error = f"Tool {tool_name} timed out after {self.timeout_seconds}s"
                logger.warning(last_error, extra={"tool": tool_name, "attempt": attempt + 1})
            
            except Exception as e:
                last_error = f"Tool {tool_name} failed: {str(e)}"
                logger.error(
                    last_error,
                    extra={"tool": tool_name, "attempt": attempt + 1, "error": str(e)},
                    exc_info=True,
                )
            
            # Increment retry count
            retry_count = attempt + 1
            
            # Wait before retry (exponential backoff)
            if attempt < self.max_retries:
                wait_time = min(2 ** attempt, 10.0)  # 1s, 2s, 4s, 8s, 10s max
                logger.debug(f"Retrying tool {tool_name} in {wait_time}s...")
                await asyncio.sleep(wait_time)
        
        # All retries failed
        latency_ms = (time.perf_counter() - start) * 1000
        
        # Update circuit breaker
        if self.enable_circuit_breaker:
            self._record_failure(tool_name)
        
        logger.error(
            f"Tool {tool_name} failed after {self.max_retries} retries",
            extra={
                "tool": tool_name,
                "error": last_error,
                "latency_ms": latency_ms,
                "retry_count": retry_count,
            },
        )
        
        return ToolExecutionResult(
            tool_name=tool_name,
            success=False,
            error=last_error,
            latency_ms=latency_ms,
            retry_count=retry_count,
            metadata={"trace_id": trace_id} if trace_id else {},
        )
    
    async def _execute_tool(
        self,
        func: Callable,
        input_data: dict[str, Any],
        metadata: ToolMetadata,
    ) -> Any:
        """Execute tool function with input validation."""
        # Validate input against schema
        try:
            validated_input = metadata.input_schema(**input_data)
        except Exception as e:
            raise ValueError(f"Invalid input for tool {metadata.name}: {e}")
        
        # Execute tool
        result = await func(validated_input)
        
        # Validate output against schema
        if not isinstance(result, metadata.output_schema):
            try:
                result = metadata.output_schema.model_validate(result)
            except Exception as e:
                raise ValueError(f"Invalid output from tool {metadata.name}: {e}")
        
        return result
    
    def _is_circuit_open(self, tool_name: str) -> bool:
        """Check if circuit breaker is open for tool."""
        if tool_name not in self._circuit_breaker:
            return False
        
        cb_state = self._circuit_breaker[tool_name]
        
        # Check if threshold exceeded
        if cb_state["failures"] < self._circuit_breaker_threshold:
            return False
        
        # Check if timeout elapsed
        time_since_failure = time.time() - cb_state["last_failure"]
        if time_since_failure > self._circuit_breaker_timeout:
            # Reset circuit breaker (half-open state)
            del self._circuit_breaker[tool_name]
            return False
        
        return True
    
    def _record_failure(self, tool_name: str):
        """Record tool failure for circuit breaker."""
        if tool_name not in self._circuit_breaker:
            self._circuit_breaker[tool_name] = {"failures": 0, "last_failure": 0.0}
        
        self._circuit_breaker[tool_name]["failures"] += 1
        self._circuit_breaker[tool_name]["last_failure"] = time.time()
    
    def list_tools(self) -> list[ToolMetadata]:
        """List all available tools."""
        return registry.list_tools()
    
    def get_tool_metadata(self, tool_name: str) -> ToolMetadata | None:
        """Get metadata for specific tool."""
        tool_info = registry.get_tool(tool_name)
        return tool_info[0] if tool_info else None
    
    def to_openai_tools(self) -> list[dict]:
        """
        Convert all tools to OpenAI function calling format.
        
        Used for integration with OpenAI-compatible APIs (GPT-4, Claude, etc.)
        """
        return registry.to_openai_tools()
    
    def get_tools_by_category(self, category: str) -> list[ToolMetadata]:
        """Get tools filtered by category."""
        return registry.get_tools_by_category(category)
    
    def get_tools_by_tags(self, tags: list[str]) -> list[ToolMetadata]:
        """Get tools that have any of the specified tags."""
        all_tools = self.list_tools()
        return [t for t in all_tools if any(tag in t.tags for tag in tags)]
    
    def reset_circuit_breaker(self, tool_name: str | None = None):
        """Reset circuit breaker for specific tool or all tools."""
        if tool_name:
            if tool_name in self._circuit_breaker:
                del self._circuit_breaker[tool_name]
                logger.info(f"Circuit breaker reset for tool: {tool_name}")
        else:
            self._circuit_breaker.clear()
            logger.info("All circuit breakers reset")


# Global client instance
mcp_client = MCPClient()
