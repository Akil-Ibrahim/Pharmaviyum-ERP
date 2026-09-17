"""
Health check system for monitoring dependencies
Best practice 2026: Comprehensive health checks with graceful degradation
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

from src.pharmaviyum.core.logging import get_logger

logger = get_logger(__name__)


class HealthStatus(str, Enum):
    """Health check status"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a single health check"""

    name: str
    status: HealthStatus
    latency_ms: float = 0.0
    message: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class AggregatedHealth:
    """Aggregated health status of all checks"""

    status: HealthStatus
    checks: list[HealthCheckResult]
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    version: str = ""
    environment: str = ""
    uptime_seconds: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for API response"""
        return {
            "status": self.status.value,
            "timestamp": self.timestamp,
            "version": self.version,
            "environment": self.environment,
            "uptime_seconds": round(self.uptime_seconds, 2),
            "checks": {
                check.name: {
                    "status": check.status.value,
                    "latency_ms": round(check.latency_ms, 2),
                    "message": check.message,
                    "details": check.details,
                }
                for check in self.checks
            },
        }


class HealthChecker:
    """Health checker for all system dependencies."""

    def __init__(self):
        self._checks: dict[str, dict] = {}
        self._cache: dict[str, tuple[HealthCheckResult, float]] = {}
        self._cache_ttl = 10.0
        self._start_time = datetime.now(timezone.utc)

    def register(
        self,
        name: str,
        check_fn: Callable,
        critical: bool = True,
        timeout_seconds: float = 5.0,
    ) -> None:
        self._checks[name] = {
            "fn": check_fn,
            "critical": critical,
            "timeout": timeout_seconds,
        }
        logger.debug(f"Registered health check: {name} (critical={critical})")

    async def check(self, name: str) -> HealthCheckResult:
        """Run a single health check with caching."""
        if name in self._cache:
            cached_result, cached_time = self._cache[name]
            if (datetime.now(timezone.utc).timestamp() - cached_time) < self._cache_ttl:
                return cached_result

        check_config = self._checks.get(name)
        if not check_config:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNKNOWN,
                message=f"Check '{name}' not registered",
            )

        try:
            start = datetime.now(timezone.utc)
            result = await asyncio.wait_for(
                check_config["fn"](), timeout=check_config["timeout"]
            )
            result.latency_ms = (
                datetime.now(timezone.utc) - start
            ).total_seconds() * 1000
            self._cache[name] = (result, datetime.now(timezone.utc).timestamp())
            return result
        except asyncio.TimeoutError:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check timed out after {check_config['timeout']}s",
            )
        except Exception as e:
            logger.error(f"Health check '{name}' failed: {e}", exc_info=True)
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
            )

    async def check_all(self) -> AggregatedHealth:
        """Run all health checks in parallel."""
        from src.pharmaviyum.core.config import settings

        tasks = [self.check(name) for name in self._checks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        check_results = []
        for result in results:
            if isinstance(result, Exception):
                check_results.append(
                    HealthCheckResult(
                        name="unknown",
                        status=HealthStatus.UNHEALTHY,
                        message=str(result),
                    )
                )
            else:
                check_results.append(result)

        overall_status = self._aggregate_status(check_results)
        uptime = (datetime.now(timezone.utc) - self._start_time).total_seconds()
        return AggregatedHealth(
            status=overall_status,
            checks=check_results,
            version=settings.APP_VERSION,
            environment=settings.ENVIRONMENT.value,
            uptime_seconds=uptime,
        )

    def _aggregate_status(self, results: list[HealthCheckResult]) -> HealthStatus:
        has_critical_unhealthy = False
        has_any_unhealthy = False
        has_degraded = False
        for result in results:
            check_config = self._checks.get(result.name, {})
            is_critical = check_config.get("critical", True)
            if result.status == HealthStatus.UNHEALTHY:
                if is_critical:
                    has_critical_unhealthy = True
                else:
                    has_any_unhealthy = True
            elif result.status == HealthStatus.DEGRADED:
                has_degraded = True
        if has_critical_unhealthy:
            return HealthStatus.UNHEALTHY
        if has_any_unhealthy or has_degraded:
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY

    def invalidate_cache(self, name: Optional[str] = None) -> None:
        """Invalidate health check cache."""
        if name:
            self._cache.pop(name, None)
        else:
            self._cache.clear()


health_checker = HealthChecker()


async def check_database() -> HealthCheckResult:
    """Check PostgreSQL database connectivity."""
    from sqlalchemy import text

    from src.pharmaviyum.core.database import engine

    try:
        async with engine.connect() as conn:
            start = datetime.now(timezone.utc)
            result = await conn.execute(text("SELECT 1"))
            await result.fetchone()
            latency = (datetime.now(timezone.utc) - start).total_seconds() * 1000
            pool = engine.pool
            pool_info = {
                "size": pool.size(),
                "checkedin": pool.checkedin(),
                "checkedout": pool.checkedout(),
                "overflow": pool.overflow(),
            }
            return HealthCheckResult(
                name="database",
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                message="Database connection OK",
                details=pool_info,
            )
    except Exception as e:
        return HealthCheckResult(
            name="database",
            status=HealthStatus.UNHEALTHY,
            message=f"Database connection failed: {e}",
        )


async def check_redis() -> HealthCheckResult:
    """Check Redis connectivity."""
    from redis import asyncio as aioredis

    from src.pharmaviyum.core.config import settings

    redis = None
    try:
        redis = aioredis.from_url(settings.REDIS_URL)
        start = datetime.now(timezone.utc)
        pong = await redis.ping()
        latency = (datetime.now(timezone.utc) - start).total_seconds() * 1000
        info = await redis.info("server")
        return HealthCheckResult(
            name="redis",
            status=HealthStatus.HEALTHY if pong else HealthStatus.UNHEALTHY,
            latency_ms=latency,
            message="Redis connection OK",
            details={
                "redis_version": info.get("redis_version"),
                "uptime_in_seconds": info.get("uptime_in_seconds"),
                "connected_clients": info.get("connected_clients"),
            },
        )
    except Exception as e:
        return HealthCheckResult(
            name="redis",
            status=HealthStatus.UNHEALTHY,
            message=f"Redis connection failed: {e}",
        )
    finally:
        if redis:
            await redis.close()


async def check_worker_queues() -> HealthCheckResult:
    """Check background worker queue health."""
    try:
        from src.pharmaviyum.workers.dispatcher import task_dispatcher

        queue_lengths = await task_dispatcher.get_all_queue_lengths()
        stuck_queues = [
            {"queue": queue, "length": length}
            for queue, length in queue_lengths.items()
            if length > 1000
        ]
        status = HealthStatus.DEGRADED if stuck_queues else HealthStatus.HEALTHY
        message = (
            f"{len(stuck_queues)} queues have high backlog"
            if stuck_queues
            else "All queues healthy"
        )
        return HealthCheckResult(
            name="worker_queues",
            status=status,
            message=message,
            details={
                "queue_lengths": queue_lengths,
                "stuck_queues": stuck_queues,
            },
        )
    except Exception as e:
        return HealthCheckResult(
            name="worker_queues",
            status=HealthStatus.DEGRADED,
            message=f"Queue check failed: {e}",
        )


async def check_pos_connections() -> HealthCheckResult:
    """Check POS system connections (KiotViet, Sapo, etc)."""
    from src.pharmaviyum.core.config import settings

    connections = {
        "kiotviet": settings.KIOVIET_API_URL is not None,
        "sapo": settings.SAPO_API_URL is not None,
        "viettel_pms": settings.VIETTEL_PMS_API_URL is not None,
    }
    configured = sum(1 for value in connections.values() if value)
    status = HealthStatus.HEALTHY if configured > 0 else HealthStatus.DEGRADED
    return HealthCheckResult(
        name="pos_connections",
        status=status,
        message=f"{configured} POS systems configured",
        details={"connections": connections, "total_configured": configured},
    )


async def check_disk_space() -> HealthCheckResult:
    """Check available disk space."""
    import shutil

    try:
        total, used, free = shutil.disk_usage("/")
        free_gb = free / (1024**3)
        free_percent = (free / total) * 100
        if free_percent < 5:
            status = HealthStatus.UNHEALTHY
            message = f"Critical: only {free_gb:.2f}GB free"
        elif free_percent < 20:
            status = HealthStatus.DEGRADED
            message = f"Warning: {free_gb:.2f}GB free ({free_percent:.1f}%)"
        else:
            status = HealthStatus.HEALTHY
            message = f"Disk space OK: {free_gb:.2f}GB free"
        return HealthCheckResult(
            name="disk_space",
            status=status,
            message=message,
            details={
                "total_gb": round(total / (1024**3), 2),
                "used_gb": round(used / (1024**3), 2),
                "free_gb": round(free_gb, 2),
                "free_percent": round(free_percent, 2),
            },
        )
    except Exception as e:
        return HealthCheckResult(
            name="disk_space",
            status=HealthStatus.DEGRADED,
            message=f"Disk check failed: {e}",
        )


async def check_memory() -> HealthCheckResult:
    """Check memory usage."""
    try:
        import psutil

        memory = psutil.virtual_memory()
        if memory.percent > 95:
            status = HealthStatus.UNHEALTHY
            message = f"Critical: {memory.percent}% memory used"
        elif memory.percent > 80:
            status = HealthStatus.DEGRADED
            message = f"Warning: {memory.percent}% memory used"
        else:
            status = HealthStatus.HEALTHY
            message = f"Memory OK: {memory.percent}% used"
        return HealthCheckResult(
            name="memory",
            status=status,
            message=message,
            details={
                "total_mb": round(memory.total / (1024**2), 2),
                "available_mb": round(memory.available / (1024**2), 2),
                "used_percent": memory.percent,
            },
        )
    except ImportError:
        return HealthCheckResult(
            name="memory",
            status=HealthStatus.UNKNOWN,
            message="psutil not installed",
        )
    except Exception as e:
        return HealthCheckResult(
            name="memory",
            status=HealthStatus.DEGRADED,
            message=f"Memory check failed: {e}",
        )


def register_all_health_checks() -> None:
    """Register all health checks with the health checker."""
    health_checker.register(
        "database", check_database, critical=True, timeout_seconds=5.0
    )
    health_checker.register("redis", check_redis, critical=True, timeout_seconds=3.0)
    health_checker.register(
        "worker_queues", check_worker_queues, critical=False, timeout_seconds=5.0
    )
    health_checker.register(
        "pos_connections", check_pos_connections, critical=False, timeout_seconds=5.0
    )
    health_checker.register(
        "disk_space", check_disk_space, critical=False, timeout_seconds=3.0
    )
    health_checker.register("memory", check_memory, critical=False, timeout_seconds=3.0)
    logger.info(f"Registered {len(health_checker._checks)} health checks")
