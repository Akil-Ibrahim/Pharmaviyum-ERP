"""Redis caching service using the shared instrumented client."""

from __future__ import annotations

import json
from typing import Any, Optional

from redis.asyncio import Redis

from src.pharmaviyum.ai.config import settings as ai_settings
from src.pharmaviyum.core.logging import get_logger
from src.pharmaviyum.redis_client import get_redis

logger = get_logger(__name__)


class CacheService:
    """Redis-based caching service with centralized connection management."""

    def __init__(self, redis: Redis | None = None):
        self._redis = redis

    async def _client(self) -> Redis:
        if self._redis is None:
            self._redis = await get_redis()
        return self._redis

    async def get(self, key: str) -> Optional[Any]:
        try:
            value = await (await self._client()).get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as exc:
            logger.error("Cache get error", extra={"key": key, "error": type(exc).__name__})
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        try:
            redis = await self._client()
            serialized = json.dumps(value, ensure_ascii=False)
            if ttl:
                await redis.setex(key, ttl, serialized)
            else:
                await redis.set(key, serialized)
            return True
        except Exception as exc:
            logger.error("Cache set error", extra={"key": key, "error": type(exc).__name__})
            return False

    async def delete(self, key: str) -> bool:
        try:
            await (await self._client()).delete(key)
            return True
        except Exception as exc:
            logger.error("Cache delete error", extra={"key": key, "error": type(exc).__name__})
            return False

    async def exists(self, key: str) -> bool:
        try:
            return await (await self._client()).exists(key) > 0
        except Exception as exc:
            logger.error("Cache exists error", extra={"key": key, "error": type(exc).__name__})
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        try:
            redis = await self._client()
            cursor = 0
            deleted = 0
            while True:
                cursor, keys = await redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await redis.delete(*keys)
                    deleted += len(keys)
                if cursor == 0:
                    break
            logger.info("Invalidated cache keys", extra={"deleted": deleted})
            return deleted
        except Exception as exc:
            logger.error("Cache invalidate error", extra={"error": type(exc).__name__})
            return 0

    async def close(self) -> None:
        """Shared Redis lifecycle is owned by the application, so nothing is closed here."""
        return None


cache_service = CacheService()
