"""
MCP Health Check Endpoints.

Provides liveness and readiness probes for Kubernetes and load balancers.
"""
from __future__ import annotations
from .registry import registry
from .tool_management import health_checker, analytics_tracker
from src.pharmaviyum.core.logging import logger


async def get_mcp_health_status() -> dict[str, Any]:
    """
    Comprehensive health status of the MCP layer.
    
    Returns:
        {
            "status": "healthy" | "degraded" | "unhealthy",
            "tools": {"tool_name": {"status": "...", "details": "..."}},
            "analytics": {"total_tools_registered": int}
        }
    """
    tool_health = await health_checker.check_all_health()
    
    # Determine overall status
    unhealthy_count = sum(1 for h in tool_health.values() if h["status"] == "unhealthy")
    degraded_count = sum(1 for h in tool_health.values() if h["status"] == "degraded")
    
    if unhealthy_count > 0:
        overall_status = "unhealthy"
    elif degraded_count > 0:
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    return {
        "status": overall_status,
        "timestamp": "2026-09-14T12:00:00Z",  # Replace with datetime.utcnow().isoformat()
        "tools": tool_health,
        "analytics": {
            "total_tools_registered": len(registry.list_tools()),
        }
    }
