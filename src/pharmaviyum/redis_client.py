"""
Redis client configuration and connection management.
Best Practice: Use connection pooling, bounded metrics, and proper error handling.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

import structlog
from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import ConnectionError, TimeoutError

from src.pharmaviyum.observability.metrics import (
    REDIS_COMMAND_DURATION,
    REDIS_COMMAND_ERRORS_TOTAL,
    REDIS_COMMANDS_TOTAL,
    REDIS_CONNECTION_LIMIT,
    REDIS_CONNECTIONS,
    REDIS_CONNECTIONS_AVAILABLE,
    REDIS_CONNECTIONS_IN_USE,
)
from src.pharmaviyum.config import settings

logger = structlog.get_logger()

_redis_client: Redis | None = None
_pool: ConnectionPool | None = None

T = TypeVar("T")


def _update_pool_metrics(pool: ConnectionPool) -> None:
    """Export pool state without exposing connection keys or other high-cardinality data."""
    created = getattr(pool, "_created_connections", None)
    available = getattr(pool, "_available_connections", None)
    in_use = getattr(pool, "_in_use_connections", None)

    if isinstance(created, int):
        REDIS_CONNECTIONS.set(created)
    if isinstance(available, list):
        REDIS_CONNECTIONS_AVAILABLE.set(len(available))
    if isinstance(in_use, set):
        REDIS_CONNECTIONS_IN_USE.set(len(in_use))
    REDIS_CONNECTION_LIMIT.set(settings.REDIS_MAX_CONNECTIONS)


async def _execute_redis_command(
    operation: str, command: Callable[[], Awaitable[T]]
) -> T:
    """Execute a bounded Redis operation metric without recording keys or values."""
    started = time.perf_counter()
    try:
        result = await command()
    except Exception:
        REDIS_COMMANDS_TOTAL.labels(operation=operation, status="failure").inc()
        REDIS_COMMAND_ERRORS_TOTAL.labels(operation=operation).inc()
        raise
    else:
        REDIS_COMMANDS_TOTAL.labels(operation=operation, status="success").inc()
        return result
    finally:
        REDIS_COMMAND_DURATION.labels(operation=operation).observe(
            time.perf_counter() - started
        )
        if _pool is not None:
            _update_pool_metrics(_pool)


def get_redis_pool() -> ConnectionPool:
    """Get or create the shared Redis connection pool."""
    global _pool
    if _pool is None:
        _pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=True,
        )
        _update_pool_metrics(_pool)
        logger.info("redis_connection_pool_created")
    return _pool


async def get_redis() -> Redis:
    """Get the shared Redis client and verify connectivity on first initialization."""
    global _redis_client
    if _redis_client is None:
        pool = get_redis_pool()
        _redis_client = Redis(connection_pool=pool)
        try:
            await _execute_redis_command("ping", _redis_client.ping)
            logger.info("redis_connected")
        except (ConnectionError, TimeoutError) as exc:
            logger.error("redis_connection_failed", error=str(exc))
            raise
    return _redis_client


async def close_redis() -> None:
    """Close the Redis client and connection pool."""
    global _redis_client, _pool
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
    if _pool:
        await _pool.disconnect()
        _pool = None
    REDIS_CONNECTIONS.set(0)
    REDIS_CONNECTIONS_AVAILABLE.set(0)
    REDIS_CONNECTIONS_IN_USE.set(0)
    logger.info("redis_connection_closed")


async def cache_get(key: str) -> str | None:
    """Get value from cache."""
    redis = await get_redis()
    return await _execute_redis_command("get", lambda: redis.get(key))


async def cache_set(key: str, value: str, expire: int = 3600) -> bool:
    """Set value in cache with expiration."""
    redis = await get_redis()
    return await _execute_redis_command(
        "setex", lambda: redis.setex(key, expire, value)
    )


async def cache_delete(key: str) -> int:
    """Delete key from cache."""
    redis = await get_redis()
    return await _execute_redis_command("delete", lambda: redis.delete(key))


async def cache_exists(key: str) -> bool:
    """Check if key exists in cache."""
    redis = await get_redis()
    result = await _execute_redis_command("exists", lambda: redis.exists(key))
    return result > 0
