"""
MCP Tool Registry — central registry for all available tools.

Supports:
- Tool versioning (e.g., "check_drug_interactions:v2")
- Role-Based Access Control (RBAC)
- Role-filtered tool discovery for LLM tool binding
- Trusted tenant context propagation to tool execution
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

    def configure_approval_verifier(self, verifier: ApprovalVerifier | None) -> None:
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
        execution_class: ExecutionClass | None = None,
        requires_pharmacist_confirmation: bool = False,
    ) -> Callable:
        """Decorator to register a tool."""
        # Validate the contract at decorator creation time so invalid tools
        # fail closed even before a function is registered.
        validate_tool_schema(input_schema.model_json_schema())
        if execution_class is None:
            raise ValueError(
                "MCP tools must explicitly declare execution_class='read' or 'write'"
            )
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
                required_roles=(
                    required_roles
                    if required_roles is not None
                    else ["pharmacist", "admin", "system"]
                ),
                version=version,
                deprecated=deprecated,
                deprecation_message=deprecation_message,
                execution_class=execution_class,
                requires_pharmacist_confirmation=requires_pharmacist_confirmation,
            )
            self._tools[name] = (metadata, func)
            logger.info(f"Registered MCP tool: {name} v{version} ({category})")
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
        """Call a registered tool with RBAC and trusted tenant context."""
        from .context import require_mcp_context
        from .tool_management import (
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
        if resolved_name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")

        metadata, func = self._tools[resolved_name]

        if metadata.deprecated:
            logger.warning(
                "Deprecated tool called: %s. %s",
                resolved_name,
                metadata.deprecation_message,
            )

        if not check_rbac(user_role, metadata.required_roles):
            raise PermissionError(
                f"Role '{user_role}' is not authorized to use tool '{resolved_name}'. "
                f"Required: {metadata.required_roles}"
            )

        health = await health_checker.check_tool_health(resolved_name)
        if health.get("status") != "healthy":
            raise RuntimeError("MCP tool dependency is unavailable")

        try:
            validated_input = metadata.input_schema.model_validate(input_data)
        except Exception:
            # Pydantic validation errors can echo submitted clinical values.
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

        start = time.perf_counter()
        try:
            from .context import (
                MCPAuthorizationContext,
                reset_mcp_context,
                set_mcp_context,
            )

            token = set_mcp_context(
                MCPAuthorizationContext(
                    user_id=user_id,
                    pharmacy_id=pharmacy_id,
                    user_role=user_role,
                )
            )
            try:
                result = await func(validated_input)
            finally:
                reset_mcp_context(token)

            latency_ms = (time.perf_counter() - start) * 1000
            if not isinstance(result, metadata.output_schema):
                result = metadata.output_schema.model_validate(result)

            from .tool_management import ToolUsageRecord

            analytics_tracker.record_usage(
                ToolUsageRecord(
                    tool_name=metadata.name,
                    tool_version=metadata.version,
                    user_role=user_role,
                    success=True,
                    latency_ms=latency_ms,
                )
            )
            logger.info(
                "Tool %s executed in %.2fms by %s",
                resolved_name,
                latency_ms,
                user_role,
            )
            return result
        except Exception as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "MCP tool execution failed",
                extra={
                    "tool": resolved_name,
                    "role": user_role,
                    "error_type": type(exc).__name__,
                },
            )
            from .tool_management import ToolUsageRecord

            analytics_tracker.record_usage(
                ToolUsageRecord(
                    tool_name=metadata.name,
                    tool_version=metadata.version,
                    user_role=user_role,
                    success=False,
                    latency_ms=latency_ms,
                )
            )
            raise

    def list_tools(self) -> list[ToolMetadata]:
        return [meta for meta, _ in self._tools.values()]

    def list_tools_for_role(self, user_role: UserRole) -> list[ToolMetadata]:
        """Return only tools the role is authorized to invoke."""
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
            schema = metadata.input_schema.model_json_schema()
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": metadata.name,
                        "description": metadata.description,
                        "parameters": schema,
                    },
                }
            )
        return tools

    def get_tool(self, name: str) -> tuple[ToolMetadata, Callable] | None:
        return self._tools.get(name)


registry = MCPToolRegistry()
