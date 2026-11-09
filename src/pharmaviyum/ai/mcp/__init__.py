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

from . import schemas
from .client import MCPClient, mcp_client
from .health import get_mcp_health_status
from .prompts import PromptRegistry, prompt_registry
from .registry import MCPToolRegistry
from .registry import registry as tool_registry

# Import tool modules once so decorators register the server's complete tool set.
from . import tools as _registered_tools  # noqa: F401,E402
from .resources import ResourceRegistry, resource_registry
from .server import MCPServer, mcp_server
from .tool_management import (
    analytics_tracker,
    check_rbac,
    health_checker,
    resolve_tool_version,
)

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
