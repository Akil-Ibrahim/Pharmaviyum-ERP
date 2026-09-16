"""
Task dispatcher for queueing background jobs
Best practice 2026: Centralized task dispatch with monitoring
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from redis import asyncio as aioredis

from src.pharmaviyum.core.config import settings
from src.pharmaviyum.core.logging import get_logger
from src.pharmaviyum.redis_client import get_redis
from src.pharmaviyum.workers.queues import TaskQueue

logger = get_logger(__name__)


class TaskDispatcher:
    """
    Centralized task dispatcher

    Features:
    - Task queueing to Redis
    - Priority-based routing
    - Idempotency support
    - Task tracking
    """

    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        """Initialize dispatcher.

        A Redis client may be injected for tests/isolated consumers. Normal
        application traffic uses the shared instrumented client.
        """
        self.redis = redis_client

    async def _client(self) -> aioredis.Redis:
        """Return the injected client or the shared instrumented client."""
        if self.redis is None:
            self.redis = await get_redis()
        return self.redis

    async def dispatch(
        self,
        task_name: str,
        task_args: dict[str, Any],
        queue: str = TaskQueue.NOTIFICATIONS.value,
        priority: int = 5,
        idempotency_key: Optional[str] = None,
        scheduled_at: Optional[datetime] = None,
    ) -> str:
        """Dispatch task to queue."""
        redis = await self._client()
        task_id = idempotency_key or str(uuid.uuid4())

        if idempotency_key:
            existing = await redis.get(f"task:{idempotency_key}")
            if existing:
                logger.info(
                    "Task already dispatched",
                    extra={"task_id": task_id, "task_name": task_name},
                )
                return task_id

        payload = {
            "task_id": task_id,
            "task_name": task_name,
            "task_args": task_args,
            "queue": queue,
            "priority": priority,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "queued",
        }

        await redis.setex(
            f"task:{task_id}",
            86400,
            json.dumps(payload, ensure_ascii=False),
        )

        queue_key = f"queue:{queue}"
        if scheduled_at:
            await redis.zadd(queue_key, {task_id: scheduled_at.timestamp()})
        else:
            score = (priority * 1_000_000_000) + datetime.now(timezone.utc).timestamp()
            await redis.zadd(queue_key, {task_id: score})

        logger.info(
            "Task dispatched",
            extra={
                "task_id": task_id,
                "task_name": task_name,
                "queue": queue,
                "priority": priority,
            },
        )
        return task_id

    async def get_task_status(self, task_id: str) -> Optional[dict]:
        """Get task status."""
        redis = await self._client()
        payload = await redis.get(f"task:{task_id}")
        if payload:
            return json.loads(payload)
        return None

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel queued task."""
        redis = await self._client()
        payload = await self.get_task_status(task_id)
        if not payload:
            return False

        queue = payload.get("queue")
        queue_key = f"queue:{queue}"
        removed = await redis.zrem(queue_key, task_id)

        payload["status"] = "cancelled"
        payload["cancelled_at"] = datetime.now(timezone.utc).isoformat()
        await redis.setex(
            f"task:{task_id}",
            86400,
            json.dumps(payload, ensure_ascii=False),
        )
        return removed > 0

    async def get_queue_length(self, queue: str) -> int:
        """Get number of tasks in queue."""
        redis = await self._client()
        return await redis.zcard(f"queue:{queue}")

    async def get_all_queue_lengths(self) -> dict[str, int]:
        """Get lengths of all queues."""
        return {
            queue.value: await self.get_queue_length(queue.value)
            for queue in TaskQueue
        }


# Singleton instance
task_dispatcher = TaskDispatcher()
