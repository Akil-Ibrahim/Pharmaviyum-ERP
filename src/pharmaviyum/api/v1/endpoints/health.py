"""
Health and readiness endpoints
Best practice 2026: Kubernetes-compatible health checks
"""

import sys

from fastapi import APIRouter, Request, Response

from src.pharmaviyum.ai.config import settings as application_settings
from src.pharmaviyum.build_info import BUILD_COMMIT
from src.pharmaviyum.config import settings as auth_settings
from src.pharmaviyum.core.config import settings
from src.pharmaviyum.core.health import (
    HealthStatus,
    check_database,
    check_redis,
    health_checker,
)
from src.pharmaviyum.core.metrics import APP_HEALTH_STATUS, get_metrics

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """
    Liveness probe endpoint

    Returns overall health status.
    Used by Kubernetes livenessProbe.

    Returns:
        200 if healthy or degraded
        503 if unhealthy
    """
    health = await health_checker.check_all()

    # Update metrics
    if health.status == HealthStatus.HEALTHY:
        APP_HEALTH_STATUS.state("healthy")
    elif health.status == HealthStatus.DEGRADED:
        APP_HEALTH_STATUS.state("degraded")
    elif health.status == HealthStatus.UNHEALTHY:
        APP_HEALTH_STATUS.state("unhealthy")
    else:
        APP_HEALTH_STATUS.state("unknown")

    # Return appropriate status code
    status_code = 200 if health.status != HealthStatus.UNHEALTHY else 503

    return Response(
        content=__import__("json").dumps(health.to_dict(), ensure_ascii=False),
        status_code=status_code,
        media_type="application/json",
    )


@router.get("/ready")
async def readiness_check(request: Request):
    """
    Readiness probe for production dependencies.

    Checks PostgreSQL and Redis with real read-only probes and confirms that
    the application AI container completed startup initialization.
    """
    database_result, redis_result = await check_database(), await check_redis()
    ai_initialized = bool(getattr(request.app.state, "ai_initialized", False))

    components = {
        "postgres": "ok" if database_result.status == HealthStatus.HEALTHY else "error",
        "redis": "ok" if redis_result.status == HealthStatus.HEALTHY else "error",
        "ai_initialized": "ok" if ai_initialized else "error",
    }
    all_healthy = all(value == "ok" for value in components.values())

    return Response(
        content=__import__("json").dumps(
            {
                "status": "ready" if all_healthy else "not_ready",
                "components": components,
            },
            ensure_ascii=False,
        ),
        status_code=200 if all_healthy else 503,
        media_type="application/json",
    )

@router.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint

    Returns metrics in Prometheus text format.
    Used by Prometheus server for scraping.
    """
    metrics_bytes, content_type = get_metrics()

    return Response(
        content=metrics_bytes,
        media_type=content_type,
    )


@router.get("/version")
async def version(response: Response):
    """
    Application version endpoint

    Returns version information for debugging. Runtime identity must never be
    served from an intermediary cache during production deployment verification.
    """
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return {
        "name": settings.APP_NAME,
        "build_commit": BUILD_COMMIT,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT.value,
        "debug": settings.DEBUG,
        "application_environment": application_settings.environment,
        "auth_environment": auth_settings.ENVIRONMENT,
        "auth_debug": auth_settings.DEBUG,
        "python_version": sys.version,
        "python_implementation": sys.implementation.name,
    }
