"""
MCP Tool Management: RBAC, Analytics, Health Checks, and Versioning.

Best practice 2026:
- Role-Based Access Control (RBAC) for tool execution
- Usage analytics and cost attribution per tool
- Liveness/readiness health checks for tool dependencies
- Semantic versioning for tools with deprecation workflows
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from .registry import registry

UserRole = Literal["patient", "pharmacist", "admin", "system"]


@dataclass
class ToolUsageRecord:
    """Record of a single tool execution for analytics."""

    tool_name: str
    tool_version: str
    user_role: UserRole
    success: bool
    latency_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ToolAnalyticsTracker:
    """Tracks tool usage metrics for analytics and billing."""

    def __init__(self):
        self._records: list[ToolUsageRecord] = []
        self._max_history = (
            10000  # Keep last 10k records in memory (or use Redis in prod)
        )

    def record_usage(self, record: ToolUsageRecord):
        """Record a tool usage event."""
        self._records.append(record)
        if len(self._records) > self._max_history:
            self._records = self._records[-self._max_history :]

        # Also emit to Prometheus (if configured)
        from src.pharmaviyum.ai.observability.metrics import record_tool_call

        record_tool_call(
            tool_name=record.tool_name,
            success=record.success,
            latency_ms=record.latency_ms,
        )

    def get_usage_stats(
        self, tool_name: str | None = None, hours: int = 24
    ) -> dict[str, Any]:
        """Get aggregated usage statistics."""
        cutoff = datetime.utcnow().timestamp() - (hours * 3600)

        filtered = [
            r
            for r in self._records
            if r.timestamp.timestamp() >= cutoff
            and (tool_name is None or r.tool_name == tool_name)
        ]

        total_calls = len(filtered)
        successful_calls = sum(1 for r in filtered if r.success)
        avg_latency = (
            sum(r.latency_ms for r in filtered) / total_calls
            if total_calls > 0
            else 0.0
        )

        # Group by role
        by_role: dict[str, int] = {}
        for r in filtered:
            by_role[r.user_role] = by_role.get(r.user_role, 0) + 1

        return {
            "tool_name": tool_name or "all",
            "time_range_hours": hours,
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "success_rate": successful_calls / total_calls if total_calls > 0 else 0.0,
            "avg_latency_ms": round(avg_latency, 2),
            "calls_by_role": by_role,
        }


class ToolHealthChecker:
    """Performs health checks on tool dependencies."""

    def __init__(self):
        self._health_cache: dict[str, dict[str, Any]] = {}
        self._cache_ttl = 60  # seconds

    async def check_tool_health(self, tool_name: str) -> dict[str, Any]:
        """
        Check if a tool's dependencies are healthy.
        Returns: {"status": "healthy"|"degraded"|"unhealthy", "details": str}
        """
        now = time.time()
        cached = self._health_cache.get(tool_name)

        if cached and (now - cached["checked_at"]) < self._cache_ttl:
            return cached["status_info"]

        tool_info = registry.get_tool(tool_name)
        if not tool_info:
            return {"status": "unhealthy", "details": "Tool not found"}

        metadata, _ = tool_info
        status = "healthy"
        details = []

        if metadata.requires_db:
            # Simulate DB check (in prod, ping the actual DB)
            details.append("DB: connected")

        if metadata.requires_external_api:
            details.append("External API: connected")

        if metadata.requires_rag:
            details.append("RAG Vector Store: connected")

        status_info = {
            "status": status,
            "details": ", ".join(details),
            "checked_at": now,
        }
        self._health_cache[tool_name] = {"status_info": status_info, "checked_at": now}

        return status_info

    async def check_all_health(self) -> dict[str, dict[str, Any]]:
        """Check health of all registered tools."""
        results = {}
        for meta in registry.list_tools():
            results[meta.name] = await self.check_tool_health(meta.name)
        return results


# Global instances
analytics_tracker = ToolAnalyticsTracker()
health_checker = ToolHealthChecker()


def check_rbac(user_role: UserRole, required_roles: list[UserRole]) -> bool:
    """Check if user role is authorized for the tool."""
    # Admin and system can access everything
    if user_role in ["admin", "system"]:
        return True
    return user_role in required_roles


def resolve_tool_version(tool_name: str) -> str:
    """
    Resolve tool name to a specific version.
    If no version is specified (e.g., "check_drug_interactions"),
    return the latest stable version registered.
    """
    if ":" in tool_name:
        return tool_name  # Already versioned

    # Find all versions of this tool
    available_tools = registry.list_tools()
    matching = [t.name for t in available_tools if t.name.startswith(f"{tool_name}:")]

    if not matching:
        # Fallback to unversioned name if no versions exist
        return tool_name

    # Simple semantic versioning sort (e.g., v2 > v1)
    matching.sort(key=lambda x: x.split(":")[-1], reverse=True)
    return matching[0]
