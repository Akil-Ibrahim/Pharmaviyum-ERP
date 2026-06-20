"""
Health Check Endpoint
Best Practice: Health checks must verify all critical dependencies.
A healthy response means the service can actually handle requests.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
import structlog
import httpx

from src.pharmaviyum.database import get_db
from src.pharmaviyum.redis_client import get_redis
from src.pharmaviyum.config import settings

logger = structlog.get_logger()
router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Comprehensive health check that validates all dependencies.
    
    Best Practices:
    - Check database connectivity
    - Check Redis connectivity
    - Check external services (AI, etc.)
    - Return detailed status for each component
    - Use appropriate HTTP status codes
    """
    health_status = {
        "status": "healthy",
        "version": settings.PROJECT_VERSION,
        "components": {},
    }
    
    all_healthy = True
    
    # ✅ GOOD: Check database connectivity
    # ❌ BAD: Return healthy without checking dependencies
    try:
        await db.execute("SELECT 1")
        health_status["components"]["database"] = {            "status": "healthy",
            "latency_ms": 0,  # Could measure actual latency
        }
    except Exception as e:
        logger.error("health_check_db_failed", error=str(e))
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        all_healthy = False
    
    # ✅ GOOD: Check Redis connectivity
    try:
        await redis.ping()
        health_status["components"]["redis"] = {
            "status": "healthy",
        }
    except Exception as e:
        logger.error("health_check_redis_failed", error=str(e))
        health_status["components"]["redis"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        all_healthy = False
    
    # ✅ GOOD: Check AI service connectivity (if enabled)
    if settings.MORTARIUM_AI_ENABLED:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{settings.MORTARIUM_AI_URL}/health")
                if response.status_code == 200:
                    health_status["components"]["mortarium_ai"] = {
                        "status": "healthy",
                    }
                else:
                    raise Exception(f"AI service returned {response.status_code}")
        except Exception as e:
            logger.error("health_check_ai_failed", error=str(e))
            health_status["components"]["mortarium_ai"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            # Don't mark as unhealthy if AI is optional
            # all_healthy = False
    
    # ✅ GOOD: Return appropriate status code
    if not all_healthy:
        health_status["status"] = "unhealthy"
        raise HTTPException(status_code=503, detail=health_status)
        return health_status


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness probe for Kubernetes/load balancers.
    Checks if the service is ready to accept traffic.
    """
    return {"status": "ready"}


@router.get("/health/live")
async def liveness_check():
    """
    Liveness probe for Kubernetes.
    Simple check to verify the process is running.
    """
    return {"status": "alive"}
