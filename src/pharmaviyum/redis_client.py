"""
Redis client configuration and connection management.
Best Practice: Use connection pooling and proper error handling.
"""

import structlog
from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import ConnectionError, TimeoutError

from src.pharmaviyum.config import settings

logger = structlog.get_logger()

# Global Redis client instance
_redis_client: Redis | None = None
_pool: ConnectionPool | None = None


def get_redis_pool() -> ConnectionPool:
    """
    Get or create Redis connection pool.
    Best Practice: Reuse connection pool for better performance.
    """
    global _pool
    if _pool is None:
        _pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=True,
        )
        logger.info("redis_connection_pool_created")
    return _pool


async def get_redis() -> Redis:
    """
    Get Redis client instance.
    Best Practice: Use singleton pattern for Redis connection.
    """
    global _redis_client
    if _redis_client is None:
        pool = get_redis_pool()
        _redis_client = Redis(connection_pool=pool)
        try:
            await _redis_client.ping()
            logger.info("redis_connected")
        except (ConnectionError, TimeoutError) as e:
            logger.error("redis_connection_failed", error=str(e))
            raise
    return _redis_client


async def close_redis():
    """Close Redis connection pool."""
    global _redis_client, _pool
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
    if _pool:
        await _pool.disconnect()
        _pool = None
    logger.info("redis_connection_closed")


# ============================================
# Redis Helper Functions
# Best Practice: Provide common Redis operations
# ============================================


async def cache_get(key: str) -> str | None:
    """Get value from cache."""
    redis = await get_redis()
    return await redis.get(key)


async def cache_set(key: str, value: str, expire: int = 3600) -> bool:
    """
    Set value in cache with expiration.

    Args:
        key: Cache key
        value: Value to cache
        expire: TTL in seconds (default: 1 hour)
    """
    redis = await get_redis()
    return await redis.setex(key, expire, value)


async def cache_delete(key: str) -> int:
    """Delete key from cache."""
    redis = await get_redis()
    return await redis.delete(key)


async def cache_exists(key: str) -> bool:
    """Check if key exists in cache."""
    redis = await get_redis()
    return await redis.exists(key) > 0
