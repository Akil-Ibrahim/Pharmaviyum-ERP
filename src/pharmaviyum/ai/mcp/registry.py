"""
MCP Tool Registry — central registry for all available tools.

Best practice 2026:
- Decorator-based tool registration
- Automatic schema extraction from Pydantic models
- Tool discovery for LangGraph integration
- Metadata for model routing (latency, cost, complexity)
"""
from __future__ import annotations
import time
from typing import Any, Callable, Awaitable
from dataclasses import dataclass, field
from pydantic import BaseModel
from src.pharmaviyum.core.logging import logger


@dataclass
class ToolMetadata:
    """Metadata about a registered tool."""
    name: str
    description: str
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]
    category: str  # "clinical", "administrative", "regulatory"
    latency_estimate_ms: int = 100
    requires_db: bool = False
    requires_rag: bool = False
    requires_external_api: bool = False
    tags: list[str] = field(default_factory=list)


class MCPToolRegistry:
    """
    Central registry for MCP tools.
    
    Usage:
        registry = MCPToolRegistry()
        
        @registry.tool(
            name="check_drug_interactions",
            description="Check drug-drug interactions",
            input_schema=DrugInteractionCheck,
            output_schema=InteractionCheckResult,
            category="clinical",
        )
        async def check_interactions(input: DrugInteractionCheck) -> InteractionCheckResult:
            ...
    """
    
    def __init__(self):
        self._tools: dict[str, tuple[ToolMetadata, Callable]] = {}
    
    def tool(
        self,
        name: str,
        description: str,
        input_schema: type[BaseModel],
        output_schema: type[BaseModel],
        category: str = "general",
        latency_estimate_ms: int = 100,
        requires_db: bool = False,
        requires_rag: bool = False,
        requires_external_api: bool = False,
        tags: list[str] | None = None,
    ) -> Callable:
        """Decorator to register a tool."""
        def decorator(func: Callable[..., Awaitable[Any]]) -> Callable:
            metadata = ToolMetadata(
                name=name,
                description=description,
                input_schema=input_schema,
                output_schema=output_schema,
                category=category,
                latency_estimate_ms=latency_estimate_ms,
                requires_db=requires_db,
                requires_rag=requires_rag,
                requires_external_api=requires_external_api,
                tags=tags or [],
            )
            self._tools[name] = (metadata, func)
            logger.info(f"Registered MCP tool: {name} ({category})")
            return func
        return decorator
    
    async def call_tool(self, name: str, input_data: dict[str, Any]) -> Any:
        """
        Call a registered tool with validation.
        
        Validates input against schema, executes tool, validates output.
        """
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")
        
        metadata, func = self._tools[name]
        
        # Validate input
        try:
            validated_input = metadata.input_schema(**input_data)
        except Exception as e:
            raise ValueError(f"Invalid input for tool {name}: {e}")
        
        # Execute with timing
        start = time.perf_counter()
        try:
            result = await func(validated_input)
            latency_ms = (time.perf_counter() - start) * 1000
            
            # Validate output
            if not isinstance(result, metadata.output_schema):
                result = metadata.output_schema.model_validate(result)
            
            logger.info(
                f"Tool {name} executed in {latency_ms:.2f}ms",
                extra={"tool": name, "latency_ms": latency_ms},
            )
            return result
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000
            logger.error(f"Tool {name} failed: {e}", extra={"tool": name})
            raise
    
    def list_tools(self) -> list[ToolMetadata]:
        """List all registered tools."""
        return [meta for meta, _ in self._tools.values()]
    
    def get_tool(self, name: str) -> tuple[ToolMetadata, Callable] | None:
        """Get a specific tool by name."""
        return self._tools.get(name)
    
    def get_tools_by_category(self, category: str) -> list[ToolMetadata]:
        """Get tools filtered by category."""
        return [
            meta for meta, _ in self._tools.values()
            if meta.category == category
        ]
    
    def to_openai_tools(self) -> list[dict]:
        """
        Convert tools to OpenAI function calling format.
        
        Used for integration with OpenAI-compatible APIs.
        """
        tools = []
        for meta, _ in self._tools.values():
            tools.append({
                "type": "function",
                "function": {
                    "name": meta.name,
                    "description": meta.description,
                    "parameters": meta.input_schema.model_json_schema(),
                },
            })
        return tools


# Global registry instance
registry = MCPToolRegistry()
