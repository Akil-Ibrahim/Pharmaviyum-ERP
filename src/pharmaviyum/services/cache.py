"""
Redis caching service
Best practice 2026: Distributed caching for performance
"""

import json
from typing import Any, Optional

from redis import asyncio as aioredis

from src.pharmaviyum.core.config import settings
from src.pharmaviyum.core.logging import get_logger

logger = get_logger(__name__)


class CacheService:
    """
    Redis-based caching service

    Provides async cache operations with automatic serialization.
    Used for:
    - AI response caching
    - Patient profile caching
    - Product catalog caching
    - Session storage
    """

    def __init__(self):
        """Initialize Redis connection"""
        self.redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}", extra={"key": key})
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds (None = no expiration)

        Returns:
            True if successful
        """
        try:
            serialized = json.dumps(value, ensure_ascii=False)
            if ttl:
                await self.redis.setex(key, ttl, serialized)
            else:
                await self.redis.set(key, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}", extra={"key": key})
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache

        Args:
            key: Cache key

        Returns:
            True if deleted
        """
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}", extra={"key": key})
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error: {e}", extra={"key": key})
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern

        Args:
            pattern: Redis pattern (e.g., "patient:*")

        Returns:
            Number of keys deleted
        """
        try:
            cursor = 0
            deleted = 0

            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await self.redis.delete(*keys)
                    deleted += len(keys)
                if cursor == 0:
                    break

            logger.info(f"Invalidated {deleted} keys matching '{pattern}'")
            return deleted
        except Exception as e:
            logger.error(f"Cache invalidate error: {e}", extra={"pattern": pattern})
            return 0

    async def close(self):
        """Close Redis connection"""
        await self.redis.close()


# Singleton instance
cache_service = CacheService()
