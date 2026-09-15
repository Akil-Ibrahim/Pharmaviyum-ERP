"""Monitoring API endpoints: liveness, readiness, and metrics."""

from __future__ import annotations

import asyncio

import asyncpg
from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from src.pharmaviyum.ai.config import settings
from src.pharmaviyum.ai.dependencies import ai_container
from src.pharmaviyum.ai.mcp import get_mcp_health_status
from src.pharmaviyum.ai.observability import ai_registry
from src.pharmaviyum.core.logging import logger

router = APIRouter(tags=["Monitoring"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Liveness probe: the process is running."""
    return {"status": "healthy", "service": "pharmaviyum-ai"}


async def _check_postgres() -> None:
    """Verify PostgreSQL connectivity without creating a long-lived pool."""
    url = settings.pgvector.database_url.get_secret_value()
    dsn = url.replace("postgresql+asyncpg://", "postgresql://", 1)
    conn = await asyncpg.connect(dsn, timeout=3)
    try:
        await conn.execute("SELECT 1")
    finally:
        await conn.close()


async def _check_redis() -> None:
    """Verify Redis connectivity using the configured URL."""
    import redis.asyncio as aioredis

    client = aioredis.from_url(settings.redis.url)
    try:
        await asyncio.wait_for(client.ping(), timeout=3)
    finally:
        await client.aclose()


@router.get("/ready")
async def readiness_check() -> Response:
    """Readiness probe: all critical infrastructure dependencies are reachable."""
    checks: dict[str, str] = {}
    errors: dict[str, str] = {}

    for name, check in (("postgres", _check_postgres), ("redis", _check_redis)):
        try:
            await check()
            checks[name] = "ok"
        except Exception as exc:  # readiness must report dependency failure, not crash
            checks[name] = "failed"
            errors[name] = type(exc).__name__

    checks["ai_initialized"] = "ok" if ai_container._initialized else "failed"
    if not ai_container._initialized:
        errors["ai"] = "not_initialized"

    if errors:
        logger.error(
            "Readiness check failed", extra={"failed_components": list(errors)}
        )
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "components": checks, "errors": errors},
        )

    return JSONResponse(
        status_code=200, content={"status": "ready", "components": checks}
    )


@router.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(ai_registry), media_type=CONTENT_TYPE_LATEST
    )


@router.get("/mcp/health")
async def mcp_health():
    """Detailed health status of MCP tools and dependencies."""
    return await get_mcp_health_status()
