"""
MCP (Model Context Protocol) Module.

Public API:
- mcp_server: Core JSON-RPC 2.0 server implementation
- tool_registry: Decorator-based tool registration with RBAC & versioning
- resource_registry: Passive data endpoints (URI-based)
- prompt_registry: Reusable prompt templates
- mcp_client: Production client with retry, circuit breaker, and tracing
- analytics_tracker: Tool usage analytics
- health_checker: Dependency health checks
- get_mcp_health_status: Liveness/readiness probe data
"""
from .server import MCPServer, mcp_server
from .registry import registry as tool_registry, MCPToolRegistry
from .resources import resource_registry, ResourceRegistry
from .prompts import prompt_registry, PromptRegistry
from .client import MCPClient, mcp_client
from .tool_management import analytics_tracker, health_checker, check_rbac, resolve_tool_version
from .health import get_mcp_health_status
from . import schemas

__all__ = [
    "mcp_server",
    "MCPServer",
    "tool_registry",
    "MCPToolRegistry",
    "resource_registry",
    "ResourceRegistry",
    "prompt_registry",
    "PromptRegistry",
    "mcp_client",
    "MCPClient",
    "analytics_tracker",
    "health_checker",
    "check_rbac",
    "resolve_tool_version",
    "get_mcp_health_status",
    "schemas",
]
