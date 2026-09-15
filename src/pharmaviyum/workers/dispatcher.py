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
        """Initialize dispatcher"""
        self.redis = redis_client or aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

    async def dispatch(
        self,
        task_name: str,
        task_args: dict[str, Any],
        queue: str = TaskQueue.NOTIFICATIONS.value,
        priority: int = 5,
        idempotency_key: Optional[str] = None,
        scheduled_at: Optional[datetime] = None,
    ) -> str:
        """
        Dispatch task to queue

        Args:
            task_name: Name of the task
            task_args: Task arguments
            queue: Target queue name
            priority: Task priority (1=highest, 10=lowest)
            idempotency_key: Optional idempotency key
            scheduled_at: Optional scheduled execution time

        Returns:
            Task ID
        """
        task_id = idempotency_key or str(uuid.uuid4())

        # Check idempotency
        if idempotency_key:
            existing = await self.redis.get(f"task:{idempotency_key}")
            if existing:
                logger.info(
                    "Task already dispatched",
                    extra={"task_id": task_id, "task_name": task_name},
                )
                return task_id

        # Build task payload
        payload = {
            "task_id": task_id,
            "task_name": task_name,
            "task_args": task_args,
            "queue": queue,
            "priority": priority,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "queued",
        }

        # Store task metadata
        await self.redis.setex(
            f"task:{task_id}",
            86400,  # 24 hours TTL
            json.dumps(payload, ensure_ascii=False),
        )

        # Add to queue
        queue_key = f"queue:{queue}"

        if scheduled_at:
            # Scheduled task - use sorted set with timestamp
            await self.redis.zadd(
                queue_key,
                {task_id: scheduled_at.timestamp()},
            )
        else:
            # Immediate task - use list with priority
            # Score = priority * 1B + timestamp for ordering
            score = (priority * 1_000_000_000) + datetime.now(timezone.utc).timestamp()
            await self.redis.zadd(queue_key, {task_id: score})

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
        """Get task status"""
        payload = await self.redis.get(f"task:{task_id}")
        if payload:
            return json.loads(payload)
        return None

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel queued task"""
        payload = await self.get_task_status(task_id)
        if not payload:
            return False

        queue = payload.get("queue")
        queue_key = f"queue:{queue}"

        # Remove from queue
        removed = await self.redis.zrem(queue_key, task_id)

        # Update status
        payload["status"] = "cancelled"
        payload["cancelled_at"] = datetime.now(timezone.utc).isoformat()
        await self.redis.setex(
            f"task:{task_id}",
            86400,
            json.dumps(payload, ensure_ascii=False),
        )

        return removed > 0

    async def get_queue_length(self, queue: str) -> int:
        """Get number of tasks in queue"""
        return await self.redis.zcard(f"queue:{queue}")

    async def get_all_queue_lengths(self) -> dict[str, int]:
        """Get lengths of all queues"""
        lengths = {}
        for queue in TaskQueue:
            lengths[queue.value] = await self.get_queue_length(queue.value)
        return lengths


# Singleton instance
task_dispatcher = TaskDispatcher()
