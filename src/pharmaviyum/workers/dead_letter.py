"""
Dead letter queue for failed tasks.
Best practice: preserve failed work and support controlled manual retry.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional, cast

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
        redis = await self._client()
        entry_id = str(uuid.uuid4())
        entry: dict[str, Any] = {
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
        await redis.hset(
            self.index_key, entry_id, json.dumps(entry, ensure_ascii=False)
        )
        await redis.zadd(
            self.queue_key, {entry_id: datetime.now(timezone.utc).timestamp()}
        )
        await redis.expire(self.queue_key, DEAD_LETTER_TTL)
        await redis.expire(self.index_key, DEAD_LETTER_TTL)
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
    ) -> list[dict[str, Any]]:
        redis = await self._client()
        raw_entry_ids = cast(
            list[bytes | str],
            await redis.zrevrange(self.queue_key, skip, skip + limit - 1),
        )
        if not raw_entry_ids:
            return []

        entries: list[dict[str, Any]] = []
        for raw_entry_id in raw_entry_ids:
            entry_id = (
                raw_entry_id.decode()
                if isinstance(raw_entry_id, bytes)
                else raw_entry_id
            )
            raw_entry_json = await redis.hget(self.index_key, entry_id)
            if raw_entry_json:
                entry_json = (
                    raw_entry_json.decode()
                    if isinstance(raw_entry_json, bytes)
                    else raw_entry_json
                )
                entry = json.loads(entry_json)
                if not isinstance(entry, dict):
                    continue
                if task_name and entry.get("task_name") != task_name:
                    continue
                entries.append(entry)
        return entries

    async def get_entry(self, entry_id: str) -> Optional[dict[str, Any]]:
        redis = await self._client()
        raw_entry_json = await redis.hget(self.index_key, entry_id)
        if raw_entry_json:
            entry_json = (
                raw_entry_json.decode()
                if isinstance(raw_entry_json, bytes)
                else raw_entry_json
            )
            entry = json.loads(entry_json)
            if isinstance(entry, dict):
                return entry
        return None

    async def mark_retried(self, entry_id: str) -> bool:
        entry = await self.get_entry(entry_id)
        if not entry:
            return False
        entry["status"] = "retried"
        entry["retried_at"] = datetime.now(timezone.utc).isoformat()
        redis = await self._client()
        await redis.hset(
            self.index_key, entry_id, json.dumps(entry, ensure_ascii=False)
        )
        return True

    async def mark_discarded(self, entry_id: str) -> bool:
        entry = await self.get_entry(entry_id)
        if not entry:
            return False
        entry["status"] = "discarded"
        entry["discarded_at"] = datetime.now(timezone.utc).isoformat()
        redis = await self._client()
        await redis.hset(
            self.index_key, entry_id, json.dumps(entry, ensure_ascii=False)
        )
        return True

    async def delete_entry(self, entry_id: str) -> bool:
        redis = await self._client()
        await redis.hdel(self.index_key, entry_id)
        await redis.zrem(self.queue_key, entry_id)
        return True

    async def count(self) -> int:
        redis = await self._client()
        return await redis.zcard(self.queue_key)

    async def clear_old(self, days: int = 7) -> int:
        redis = await self._client()
        cutoff = datetime.now(timezone.utc).timestamp() - (days * 24 * 3600)
        raw_old_entries = cast(
            list[bytes | str], await redis.zrangebyscore(self.queue_key, 0, cutoff)
        )
        if not raw_old_entries:
            return 0
        old_entries = [
            entry.decode() if isinstance(entry, bytes) else entry
            for entry in raw_old_entries
        ]
        for entry_id in old_entries:
            await self.delete_entry(entry_id)
        logger.info(
            "Cleared old dead letter entries", extra={"deleted": len(old_entries)}
        )
        return len(old_entries)


dead_letter_queue = DeadLetterQueue()
