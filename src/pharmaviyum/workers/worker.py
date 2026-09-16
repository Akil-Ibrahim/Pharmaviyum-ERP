"""
ARQ worker entry point
Best practice 2026: Graceful shutdown, health checks, metrics
"""

import asyncio
import json
import signal
from datetime import datetime, timezone
from typing import Optional

from redis import asyncio as aioredis

from src.pharmaviyum.core.logging import get_logger, setup_logging
from src.pharmaviyum.redis_client import get_redis, close_redis
from src.pharmaviyum.workers.dead_letter import dead_letter_queue
from src.pharmaviyum.workers.dispatcher import task_dispatcher
from src.pharmaviyum.workers.queues import TaskQueue
from src.pharmaviyum.workers.tasks.ai_tasks import (
    CheckDrugInteractionTask,
    GenerateRecommendationTask,
    ReviewPrescriptionTask,
)
from src.pharmaviyum.workers.tasks.notifications import (
    ProcessAcknowledgmentTask,
    SendMedicationReminderTask,
    SendPatientNotificationTask,
)
from src.pharmaviyum.workers.tasks.pos_sync import (
    SyncCustomersTask,
    SyncInventoryTask,
    SyncProductsTask,
    SyncSalesTask,
)
from src.pharmaviyum.workers.tasks.scheduled import (
    CleanupExpiredDataTask,
    GenerateDailyReportTask,
    ProcessDueRemindersTask,
    SyncAllPosTask,
)

setup_logging()
logger = get_logger(__name__)

TASK_REGISTRY = {
    "send_patient_notification": SendPatientNotificationTask,
    "send_medication_reminder": SendMedicationReminderTask,
    "process_acknowledgment": ProcessAcknowledgmentTask,
    "sync_products": SyncProductsTask,
    "sync_inventory": SyncInventoryTask,
    "sync_customers": SyncCustomersTask,
    "sync_sales": SyncSalesTask,
    "review_prescription": ReviewPrescriptionTask,
    "check_drug_interaction": CheckDrugInteractionTask,
    "generate_recommendation": GenerateRecommendationTask,
    "process_due_reminders": ProcessDueRemindersTask,
    "cleanup_expired_data": CleanupExpiredDataTask,
    "generate_daily_report": GenerateDailyReportTask,
    "sync_all_pos": SyncAllPosTask,
}


class Worker:
    """Background job worker with shared Redis instrumentation."""

    def __init__(self, queues: Optional[list[str]] = None):
        self.queues = queues or [
            q.value for q in TaskQueue if q != TaskQueue.DEAD_LETTER
        ]
        self.redis: Optional[aioredis.Redis] = None
        self._shutdown_event = asyncio.Event()
        self._tasks: list[asyncio.Task] = []
        self._stats = {
            "started_at": None,
            "processed": 0,
            "failed": 0,
            "queues": {},
        }

    async def start(self):
        """Start worker."""
        logger.info("Starting worker", extra={"queues": self.queues})
        self.redis = await get_redis()
        self._stats["started_at"] = datetime.now(timezone.utc).isoformat()

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))

        for queue in self.queues:
            self._tasks.append(asyncio.create_task(self._process_queue(queue)))

        self._tasks.append(asyncio.create_task(self._run_scheduler()))
        await self._shutdown_event.wait()
        await self._cleanup()

    async def shutdown(self):
        """Request graceful shutdown."""
        logger.info("Shutdown requested")
        self._shutdown_event.set()

    async def _process_queue(self, queue: str):
        """Process tasks from a specific queue."""
        logger.info(f"Processing queue: {queue}")
        while not self._shutdown_event.is_set():
            try:
                result = await self.redis.bzpopmin(f"queue:{queue}", timeout=1.0)
                if not result:
                    continue

                _, task_id, _ = result
                payload_json = await self.redis.get(f"task:{task_id}")
                if not payload_json:
                    logger.warning(f"Task payload not found: {task_id}")
                    continue

                payload = json.loads(payload_json)
                task_name = payload.get("task_name")
                task_args = payload.get("task_args", {})
                task_class = TASK_REGISTRY.get(task_name)
                if not task_class:
                    logger.error(f"Unknown task: {task_name}")
                    await self._mark_failed(task_id, f"Unknown task: {task_name}")
                    continue

                task_instance = task_class()
                result = await task_instance.run_with_retry(**task_args)
                self._stats["processed"] += 1
                if not result.success:
                    self._stats["failed"] += 1
                    await dead_letter_queue.add(
                        task_name=task_name,
                        task_args=task_args,
                        result=result,
                        original_queue=queue,
                    )
                await self._mark_completed(task_id, result)
            except Exception as e:
                logger.error(f"Queue processor error: {e}", exc_info=True)
                await asyncio.sleep(1.0)

    async def _mark_completed(self, task_id: str, result):
        """Mark task as completed."""
        payload_json = await self.redis.get(f"task:{task_id}")
        if payload_json:
            payload = json.loads(payload_json)
            payload["status"] = "completed" if result.success else "failed"
            payload["completed_at"] = datetime.now(timezone.utc).isoformat()
            payload["result"] = {
                "success": result.success,
                "error": result.error,
                "duration_ms": result.duration_ms,
                "attempts": result.attempts,
            }
            await self.redis.setex(
                f"task:{task_id}", 86400, json.dumps(payload, ensure_ascii=False)
            )

    async def _mark_failed(self, task_id: str, error: str):
        """Mark task as failed."""
        payload_json = await self.redis.get(f"task:{task_id}")
        if payload_json:
            payload = json.loads(payload_json)
            payload["status"] = "failed"
            payload["error"] = error
            payload["failed_at"] = datetime.now(timezone.utc).isoformat()
            await self.redis.setex(
                f"task:{task_id}", 86400, json.dumps(payload, ensure_ascii=False)
            )

    async def _run_scheduler(self):
        """Run scheduled tasks periodically."""
        logger.info("Starting scheduler")
        schedules = {
            "process_due_reminders": 60,
            "cleanup_expired_data": 24 * 3600,
            "generate_daily_report": 24 * 3600,
        }
        last_run = {name: 0 for name in schedules}
        while not self._shutdown_event.is_set():
            now = datetime.now(timezone.utc).timestamp()
            for task_name, interval in schedules.items():
                if now - last_run[task_name] >= interval:
                    try:
                        await task_dispatcher.dispatch(
                            task_name=task_name,
                            task_args={},
                            queue=TaskQueue.CLEANUP.value,
                        )
                        last_run[task_name] = now
                    except Exception as e:
                        logger.error(f"Scheduler error for {task_name}: {e}")
            await asyncio.sleep(1.0)

    async def _cleanup(self):
        """Cleanup on shutdown."""
        logger.info("Cleaning up worker")
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        await close_redis()
        logger.info("Worker shutdown complete")

    def get_stats(self) -> dict:
        """Get worker statistics."""
        return self._stats


async def run_worker(queues: Optional[list[str]] = None):
    """Run worker main entry point."""
    worker = Worker(queues=queues)
    await worker.start()


if __name__ == "__main__":
    import sys

    queues = sys.argv[1:] if len(sys.argv) > 1 else None
    asyncio.run(run_worker(queues=queues))
