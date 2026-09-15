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

from src.pharmaviyum.core.config import settings
from src.pharmaviyum.core.logging import get_logger, setup_logging
from src.pharmaviyum.workers.dead_letter import dead_letter_queue
from src.pharmaviyum.workers.dispatcher import task_dispatcher
from src.pharmaviyum.workers.queues import TaskQueue
from src.pharmaviyum.workers.tasks.ai_tasks import (
    CheckDrugInteractionTask,
    GenerateRecommendationTask,
    ReviewPrescriptionTask,
)

# Import all tasks
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

# Setup logging
setup_logging()
logger = get_logger(__name__)


# Task registry
TASK_REGISTRY = {
    # Notifications
    "send_patient_notification": SendPatientNotificationTask,
    "send_medication_reminder": SendMedicationReminderTask,
    "process_acknowledgment": ProcessAcknowledgmentTask,
    # POS Sync
    "sync_products": SyncProductsTask,
    "sync_inventory": SyncInventoryTask,
    "sync_customers": SyncCustomersTask,
    "sync_sales": SyncSalesTask,
    # AI Tasks
    "review_prescription": ReviewPrescriptionTask,
    "check_drug_interaction": CheckDrugInteractionTask,
    "generate_recommendation": GenerateRecommendationTask,
    # Scheduled
    "process_due_reminders": ProcessDueRemindersTask,
    "cleanup_expired_data": CleanupExpiredDataTask,
    "generate_daily_report": GenerateDailyReportTask,
    "sync_all_pos": SyncAllPosTask,
}


class Worker:
    """
    Background job worker

    Features:
    - Multi-queue processing
    - Graceful shutdown
    - Health monitoring
    - Metrics collection
    """

    def __init__(self, queues: Optional[list[str]] = None):
        """
        Initialize worker

        Args:
            queues: List of queues to process (default: all)
        """
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
        """Start worker"""
        logger.info("Starting worker", extra={"queues": self.queues})

        # Connect to Redis
        self.redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

        self._stats["started_at"] = datetime.now(timezone.utc).isoformat()

        # Setup signal handlers
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))

        # Start queue processors
        for queue in self.queues:
            task = asyncio.create_task(self._process_queue(queue))
            self._tasks.append(task)

        # Start scheduler for periodic tasks
        scheduler_task = asyncio.create_task(self._run_scheduler())
        self._tasks.append(scheduler_task)

        # Wait for shutdown
        await self._shutdown_event.wait()

        # Cleanup
        await self._cleanup()

    async def shutdown(self):
        """Request graceful shutdown"""
        logger.info("Shutdown requested")
        self._shutdown_event.set()

    async def _process_queue(self, queue: str):
        """Process tasks from a specific queue"""
        logger.info(f"Processing queue: {queue}")

        while not self._shutdown_event.is_set():
            try:
                # Get next task from queue
                result = await self.redis.bzpopmin(f"queue:{queue}", timeout=1.0)

                if not result:
                    continue

                _, task_id, _ = result

                # Fetch task payload
                payload_json = await self.redis.get(f"task:{task_id}")
                if not payload_json:
                    logger.warning(f"Task payload not found: {task_id}")
                    continue

                payload = json.loads(payload_json)
                task_name = payload.get("task_name")
                task_args = payload.get("task_args", {})

                # Get task class
                task_class = TASK_REGISTRY.get(task_name)
                if not task_class:
                    logger.error(f"Unknown task: {task_name}")
                    await self._mark_failed(task_id, f"Unknown task: {task_name}")
                    continue

                # Execute task
                task_instance = task_class()
                result = await task_instance.run_with_retry(**task_args)

                # Update stats
                self._stats["processed"] += 1
                if not result.success:
                    self._stats["failed"] += 1

                    # Add to dead letter queue
                    await dead_letter_queue.add(
                        task_name=task_name,
                        task_args=task_args,
                        result=result,
                        original_queue=queue,
                    )

                # Mark as completed
                await self._mark_completed(task_id, result)

            except Exception as e:
                logger.error(f"Queue processor error: {e}", exc_info=True)
                await asyncio.sleep(1.0)

    async def _mark_completed(self, task_id: str, result):
        """Mark task as completed"""
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
                f"task:{task_id}",
                86400,
                json.dumps(payload, ensure_ascii=False),
            )

    async def _mark_failed(self, task_id: str, error: str):
        """Mark task as failed"""
        payload_json = await self.redis.get(f"task:{task_id}")
        if payload_json:
            payload = json.loads(payload_json)
            payload["status"] = "failed"
            payload["error"] = error
            payload["failed_at"] = datetime.now(timezone.utc).isoformat()
            await self.redis.setex(
                f"task:{task_id}",
                86400,
                json.dumps(payload, ensure_ascii=False),
            )

    async def _run_scheduler(self):
        """Run scheduled tasks periodically"""
        logger.info("Starting scheduler")

        schedules = {
            "process_due_reminders": 60,  # Every minute
            "cleanup_expired_data": 24 * 3600,  # Daily
            "generate_daily_report": 24 * 3600,  # Daily
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
        """Cleanup on shutdown"""
        logger.info("Cleaning up worker")

        # Cancel all tasks
        for task in self._tasks:
            task.cancel()

        # Wait for tasks to finish
        await asyncio.gather(*self._tasks, return_exceptions=True)

        # Close Redis
        if self.redis:
            await self.redis.close()

        logger.info("Worker shutdown complete")

    def get_stats(self) -> dict:
        """Get worker statistics"""
        return self._stats


async def run_worker(queues: Optional[list[str]] = None):
    """Run worker main entry point"""
    worker = Worker(queues=queues)
    await worker.start()


if __name__ == "__main__":
    import sys

    # Parse queue arguments
    queues = None
    if len(sys.argv) > 1:
        queues = sys.argv[1:]

    asyncio.run(run_worker(queues=queues))
