"""
Health and readiness endpoints
Best practice 2026: Kubernetes-compatible health checks
"""
from fastapi import APIRouter, Response
from src.pharmaviyum.core.health import health_checker, HealthStatus
from src.pharmaviyum.core.metrics import get_metrics, APP_HEALTH_STATUS
from src.pharmaviyum.core.config import settings

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
async def readiness_check():
    """
    Readiness probe endpoint
    
    Checks if application is ready to accept traffic.
    Used by Kubernetes readinessProbe.
    
    Returns:
        200 if ready
        503 if not ready
    """
    # For readiness, we check only critical dependencies
    critical_checks = ["database", "redis"]
    
    results = []
    all_healthy = True
    
    for check_name in critical_checks:
        result = await health_checker.check(check_name)
        results.append(result)
        if result.status != HealthStatus.HEALTHY:
            all_healthy = False
    
    status_code = 200 if all_healthy else 503
    
    return Response(
        content=__import__("json").dumps({
            "status": "ready" if all_healthy else "not_ready",
            "checks": {
                r.name: {
                    "status": r.status.value,
                    "message": r.message,
                }
                for r in results
            },
        }, ensure_ascii=False),
        status_code=status_code,
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
async def version():
    """
    Application version endpoint
    
    Returns version information for debugging.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT.value,
        "python_version": __import__("sys").version,
    }
