"""
MCP Tool Registry — central registry for all available tools.

Updated to support:
- Tool versioning (e.g., "check_drug_interactions:v2")
- Role-Based Access Control (RBAC)
"""
from __future__ import annotations
import time
from typing import Any, Callable, Awaitable, Literal
from dataclasses import dataclass, field
from pydantic import BaseModel
from src.pharmaviyum.core.logging import logger

UserRole = Literal["patient", "pharmacist", "admin", "system"]

@dataclass
class ToolMetadata:
    """Metadata about a registered tool."""
    name: str
    description: str
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]
    category: str
    latency_estimate_ms: int = 100
    requires_db: bool = False
    requires_rag: bool = False
    requires_external_api: bool = False
    tags: list[str] = field(default_factory=list)
    # NEW: RBAC and Versioning
    required_roles: list[UserRole] = field(default_factory=lambda: ["pharmacist", "admin", "system"])
    version: str = "1.0.0"
    deprecated: bool = False
    deprecation_message: str | None = None


class MCPToolRegistry:
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
        required_roles: list[UserRole] | None = None,
        version: str = "1.0.0",
        deprecated: bool = False,
        deprecation_message: str | None = None,
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
                required_roles=required_roles or ["pharmacist", "admin", "system"],
                version=version,
                deprecated=deprecated,
                deprecation_message=deprecation_message,
            )
            self._tools[name] = (metadata, func)
            logger.info(f"Registered MCP tool: {name} v{version} ({category})")
            return func
        return decorator
    
    async def call_tool(self, name: str, input_data: dict[str, Any], user_role: UserRole = "system") -> Any:
        """Call a registered tool with RBAC and validation."""
        from .tool_management import resolve_tool_version, check_rbac, analytics_tracker, health_checker
        import time
        
        # 1. Resolve version
        resolved_name = resolve_tool_version(name)
        
        if resolved_name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")
        
        metadata, func = self._tools[resolved_name]
        
        # 2. Check deprecation
        if metadata.deprecated:
            logger.warning(f"Deprecated tool called: {resolved_name}. {metadata.deprecation_message}")
        
        # 3. Check RBAC
        if not check_rbac(user_role, metadata.required_roles):
            raise PermissionError(f"Role '{user_role}' is not authorized to use tool '{resolved_name}'. Required: {metadata.required_roles}")
        
        # 4. Health check (lightweight)
        health = await health_checker.check_tool_health(resolved_name)
        if health["status"] == "unhealthy":
            raise RuntimeError(f"Tool dependency unhealthy: {health['details']}")
        
        # 5. Validate input
        try:
            validated_input = metadata.input_schema(**input_data)
        except Exception as e:
            raise ValueError(f"Invalid input for tool {resolved_name}: {e}")
        
        # 6. Execute with timing
        start = time.perf_counter()
        try:
            result = await func(validated_input)
            latency_ms = (time.perf_counter() - start) * 1000
            
            # Validate output
            if not isinstance(result, metadata.output_schema):
                result = metadata.output_schema.model_validate(result)
            
            # 7. Record analytics
            from .tool_management import ToolUsageRecord
            analytics_tracker.record_usage(ToolUsageRecord(
                tool_name=metadata.name,
                tool_version=metadata.version,
                user_role=user_role,
                success=True,
                latency_ms=latency_ms,
            ))
            
            logger.info(f"Tool {resolved_name} executed in {latency_ms:.2f}ms by {user_role}")
            return result
            
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000
            logger.error(f"Tool {resolved_name} failed: {e}", extra={"tool": resolved_name, "role": user_role})
            
            # Record failure in analytics
            from .tool_management import ToolUsageRecord
            analytics_tracker.record_usage(ToolUsageRecord(
                tool_name=metadata.name,
                tool_version=metadata.version,
                user_role=user_role,
                success=False,
                latency_ms=latency_ms,
            ))
            raise
    
    def list_tools(self) -> list[ToolMetadata]:
        return [meta for meta, _ in self._tools.values()]
    
    def get_tool(self, name: str) -> tuple[ToolMetadata, Callable] | None:
        return self._tools.get(name)


registry = MCPToolRegistry()
