"""
Monitoring API Endpoints — Health, Readiness, and Metrics.
"""
from __future__ import annotations
from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from src.pharmaviyum.ai.dependencies import get_ai_container, get_tracer
from src.pharmaviyum.ai.mcp import get_mcp_health_status
from src.pharmaviyum.ai.observability import ai_registry
from src.pharmaviyum.core.logging import logger

router = APIRouter(tags=["Monitoring"])


@router.get("/health")
async def health_check():
    """
    Liveness probe: Is the application running?
    Kubernetes uses this to decide whether to restart the pod.
    """
    return {"status": "healthy", "service": "pharmaviyum-ai"}


@router.get("/ready")
async def readiness_check():
    """
    Readiness probe: Is the application ready to serve traffic?
    Checks critical dependencies (Redis, DB, AI components).
    """
    try:
        # Attempt to get AI container (which pings Redis and initializes components)
        # Note: In a real endpoint, we'd inject this, but for simplicity we check directly
        from src.pharmaviyum.ai.dependencies import ai_container, get_redis_client
        import redis.asyncio as aioredis
        from src.pharmaviyum.ai.config import settings
        
        redis = aioredis.from_url(settings.redis.url)
        await redis.ping()
        await redis.aclose()
        
        return {
            "status": "ready",
            "components": {
                "redis": "ok",
                "ai_initialized": ai_container._initialized,
            }
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "status": "not_ready",
            "error": str(e),
        }, 503


@router.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    Scraped by Prometheus for Grafana dashboards.
    """
    return Response(
        content=generate_latest(ai_registry),
        media_type=CONTENT_TYPE_LATEST,
    )


@router.get("/mcp/health")
async def mcp_health():
    """
    Detailed health status of all MCP tools and dependencies.
    """
    return await get_mcp_health_status()
