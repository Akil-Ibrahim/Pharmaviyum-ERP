"""
MCP Tool Registry — central registry for all available tools.

Security guarantees:
- Role-filtered tool discovery and runtime RBAC.
- Authenticated tenant context is mandatory and cannot be supplied by model arguments.
- Write tools fail closed unless a trusted, one-time approval verifier is configured.
- Tool inputs and exception details are never copied into application logs.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Literal

from pydantic import BaseModel

from src.pharmaviyum.core.logging import logger

from .security import ExecutionClass, validate_execution_policy, validate_tool_schema

UserRole = Literal["patient", "pharmacist", "admin", "system"]
ApprovalVerifier = Callable[[Any, "ToolMetadata", BaseModel], Awaitable[bool]]


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
    required_roles: list[UserRole] = field(
        default_factory=lambda: ["pharmacist", "admin", "system"]
    )
    version: str = "1.0.0"
    deprecated: bool = False
    deprecation_message: str | None = None
    execution_class: ExecutionClass = "read"
    requires_pharmacist_confirmation: bool = False


class MCPToolRegistry:
    def __init__(self, approval_verifier: ApprovalVerifier | None = None):
        self._tools: dict[str, tuple[ToolMetadata, Callable]] = {}
        self._approval_verifier = approval_verifier

    def configure_approval_verifier(
        self, verifier: ApprovalVerifier | None
    ) -> None:
        """Install a trusted verifier that atomically consumes human approvals.

        The verifier must validate the authenticated actor, tenant, exact
        canonical action payload, expiry and one-time approval state. Until
        such a verifier is configured, every write tool is denied.
        """
        self._approval_verifier = verifier

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
        execution_class: ExecutionClass = "read",
        requires_pharmacist_confirmation: bool = False,
    ) -> Callable:
        """Decorator to register a tool."""
        validate_tool_schema(input_schema.model_json_schema())
        validate_execution_policy(execution_class, requires_pharmacist_confirmation)

        if not name or not name.strip():
            raise ValueError("MCP tool name must not be empty")
        if required_roles is not None and not required_roles:
            raise ValueError("MCP tool required_roles must not be empty")

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
                required_roles=required_roles
                if required_roles is not None
                else ["pharmacist", "admin", "system"],
                version=version,
                deprecated=deprecated,
                deprecation_message=deprecation_message,
                execution_class=execution_class,
                requires_pharmacist_confirmation=requires_pharmacist_confirmation,
            )
            self._tools[name] = (metadata, func)
            logger.info("Registered MCP tool: %s v%s (%s)", name, version, category)
            return func

        return decorator

    async def call_tool(
        self,
        name: str,
        input_data: dict[str, Any],
        user_role: UserRole,
        user_id: int | None = None,
        pharmacy_id: int | None = None,
    ) -> Any:
        """Execute a tool only within a matching authenticated request context."""
        from .context import require_mcp_context
        from .tool_management import (
            ToolUsageRecord,
            analytics_tracker,
            check_rbac,
            health_checker,
            resolve_tool_version,
        )

        context = require_mcp_context()
        if (
            user_id is None
            or pharmacy_id is None
            or context.user_id != user_id
            or context.pharmacy_id != pharmacy_id
            or context.user_role != user_role
        ):
            raise PermissionError("MCP authorization context mismatch")

        resolved_name = resolve_tool_version(name)
        tool_entry = self._tools.get(resolved_name)
        if tool_entry is None:
            raise ValueError("Unknown MCP tool")

        metadata, func = tool_entry
        if metadata.deprecated:
            logger.warning("Deprecated MCP tool invoked: %s", resolved_name)

        if not check_rbac(context.user_role, metadata.required_roles):
            raise PermissionError("MCP tool access denied")

        try:
            validated_input = metadata.input_schema.model_validate(input_data)
        except Exception:
            # Pydantic validation errors may echo submitted clinical values.
            raise ValueError("Invalid MCP tool input") from None

        if metadata.execution_class == "write":
            verifier = self._approval_verifier
            if not metadata.requires_pharmacist_confirmation or verifier is None:
                raise PermissionError(
                    "MCP write execution is disabled until a trusted approval "
                    "workflow is configured"
                )
            approved = await verifier(context, metadata, validated_input)
            if approved is not True:
                raise PermissionError("MCP write action has no valid approval")

        health = await health_checker.check_tool_health(resolved_name)
        if health.get("status") != "healthy":
            raise RuntimeError("MCP tool dependency is unavailable")

        start = time.perf_counter()
        try:
            result = await func(validated_input)
            if not isinstance(result, metadata.output_schema):
                result = metadata.output_schema.model_validate(result)

            latency_ms = (time.perf_counter() - start) * 1000
            analytics_tracker.record_usage(
                ToolUsageRecord(
                    tool_name=metadata.name,
                    tool_version=metadata.version,
                    user_role=context.user_role,
                    success=True,
                    latency_ms=latency_ms,
                )
            )
            logger.info(
                "MCP tool executed: %s in %.2fms",
                resolved_name,
                latency_ms,
            )
            return result
        except Exception as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            analytics_tracker.record_usage(
                ToolUsageRecord(
                    tool_name=metadata.name,
                    tool_version=metadata.version,
                    user_role=context.user_role,
                    success=False,
                    latency_ms=latency_ms,
                )
            )
            # Never serialize exception text/tracebacks into logs: drivers and
            # validators can include SQL, identifiers or patient data.
            logger.error(
                "MCP tool execution failed",
                extra={
                    "tool": resolved_name,
                    "role": context.user_role,
                    "error_type": type(exc).__name__,
                },
            )
            raise

    def list_tools(self) -> list[ToolMetadata]:
        """Return all metadata for trusted internal administration only."""
        return [meta for meta, _ in self._tools.values()]

    def list_tools_for_role(self, user_role: UserRole) -> list[ToolMetadata]:
        """Return only tools the authenticated role may invoke."""
        from .tool_management import check_rbac

        return [
            meta
            for meta, _ in self._tools.values()
            if check_rbac(user_role, meta.required_roles)
        ]

    def to_openai_tools(self, user_role: UserRole) -> list[dict[str, Any]]:
        """Build OpenAI-compatible tool schemas after RBAC filtering."""
        tools: list[dict[str, Any]] = []
        for metadata in self.list_tools_for_role(user_role):
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": metadata.name,
                        "description": metadata.description,
                        "parameters": metadata.input_schema.model_json_schema(),
                    },
                }
            )
        return tools

    def get_tool(self, name: str) -> tuple[ToolMetadata, Callable] | None:
        return self._tools.get(name)


registry = MCPToolRegistry()
