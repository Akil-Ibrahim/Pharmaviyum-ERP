"""
Dead letter queue for failed tasks
Best practice 2026: Never lose failed tasks, enable manual retry
"""

import json
from datetime import datetime, timezone
from typing import Any, Awaitable, Optional, cast

from redis import asyncio as aioredis

from src.pharmaviyum.core.logging import get_logger
from src.pharmaviyum.redis_client import get_redis
from src.pharmaviyum.workers.base import TaskResult

logger = get_logger(__name__)

DEAD_LETTER_TTL = 30 * 24 * 3600


class DeadLetterQueue:
    """Dead letter queue for storing failed tasks."""

    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        self.redis = redis_client
        self.queue_key = "dead_letter_queue"
        self.index_key = "dead_letter_index"

    async def _client(self) -> aioredis.Redis:
        if self.redis is None:
            self.redis = await get_redis()
        return self.redis

    async def add(
        self,
        task_name: str,
        task_args: dict[str, Any],
        result: TaskResult,
        original_queue: str,
    ) -> str:
        import uuid

        redis = await self._client()
        entry_id = str(uuid.uuid4())
        entry = {
            "id": entry_id,
            "task_name": task_name,
            "task_args": task_args,
            "original_queue": original_queue,
            "error": result.error,
            "attempts": result.attempts,
            "duration_ms": result.duration_ms,
            "failed_at": datetime.now(timezone.utc).isoformat(),
            "status": "failed",
        }
        await cast(
            Awaitable[int],
            redis.hset(
                self.index_key, entry_id, json.dumps(entry, ensure_ascii=False)
            ),
        )
        await cast(
            Awaitable[int],
            redis.zadd(
                self.queue_key, {entry_id: datetime.now(timezone.utc).timestamp()}
            ),
        )
        await cast(Awaitable[bool], redis.expire(self.queue_key, DEAD_LETTER_TTL))
        await cast(Awaitable[bool], redis.expire(self.index_key, DEAD_LETTER_TTL))
        logger.error(
            "Task added to dead letter queue",
            extra={"task_name": task_name, "attempts": result.attempts},
        )
        return entry_id

    async def list_entries(
        self,
        skip: int = 0,
        limit: int = 50,
        task_name: Optional[str] = None,
    ) -> list[dict]:
        redis = await self._client()
        entry_ids = await cast(
            Awaitable[list[Any]],
            redis.zrevrange(self.queue_key, skip, skip + limit - 1),
        )
        if not entry_ids:
            return []
        entries = []
        for entry_id in entry_ids:
            entry_json = await cast(Awaitable[Any], redis.hget(self.index_key, entry_id))
            if entry_json:
                entry = json.loads(entry_json)
                if task_name and entry.get("task_name") != task_name:
                    continue
                entries.append(entry)
        return entries

    async def get_entry(self, entry_id: str) -> Optional[dict]:
        redis = await self._client()
        entry_json = await cast(Awaitable[Any], redis.hget(self.index_key, entry_id))
        if entry_json:
            return json.loads(entry_json)
        return None

    async def mark_retried(self, entry_id: str) -> bool:
        entry = await self.get_entry(entry_id)
        if not entry:
            return False
        entry["status"] = "retried"
        entry["retried_at"] = datetime.now(timezone.utc).isoformat()
        redis = await self._client()
        await cast(
            Awaitable[int],
            redis.hset(
                self.index_key, entry_id, json.dumps(entry, ensure_ascii=False)
            ),
        )
        return True

    async def mark_discarded(self, entry_id: str) -> bool:
        entry = await self.get_entry(entry_id)
        if not entry:
            return False
        entry["status"] = "discarded"
        entry["discarded_at"] = datetime.now(timezone.utc).isoformat()
        redis = await self._client()
        await cast(
            Awaitable[int],
            redis.hset(
                self.index_key, entry_id, json.dumps(entry, ensure_ascii=False)
            ),
        )
        return True

    async def delete_entry(self, entry_id: str) -> bool:
        redis = await self._client()
        await cast(Awaitable[int], redis.hdel(self.index_key, entry_id))
        await cast(Awaitable[int], redis.zrem(self.queue_key, entry_id))
        return True

    async def count(self) -> int:
        return await cast(Awaitable[int], (await self._client()).zcard(self.queue_key))

    async def clear_old(self, days: int = 7) -> int:
        redis = await self._client()
        cutoff = datetime.now(timezone.utc).timestamp() - (days * 24 * 3600)
        old_entries = await cast(
            Awaitable[list[Any]],
            redis.zrangebyscore(self.queue_key, 0, cutoff),
        )
        if not old_entries:
            return 0
        for entry_id in old_entries:
            await self.delete_entry(entry_id)
        logger.info(
            "Cleared old dead letter entries", extra={"deleted": len(old_entries)}
        )
        return len(old_entries)


dead_letter_queue = DeadLetterQueue()
