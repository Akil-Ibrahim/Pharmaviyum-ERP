"""
Celery Application Configuration for Document Ingestion.

Best practice 2026:
- Redis as broker and result backend
- Task routing for different ingestion workloads
- Retry policies with exponential backoff
- Task priority queues for urgent documents
- Low-cardinality Prometheus task telemetry
"""

from __future__ import annotations

import time
from threading import Lock

from celery import Celery, signals

from src.pharmaviyum.ai.observability.metrics import (
    CELERY_TASK_DURATION,
    CELERY_TASKS_IN_FLIGHT,
    CELERY_TASKS_TOTAL,
)
from src.pharmaviyum.core.config import settings
from src.pharmaviyum.core.logging import logger

_TASK_START_TIMES: dict[str, tuple[float, str, str]] = {}
_TASK_START_LOCK = Lock()
_ALLOWED_QUEUES = {"ingestion", "maintenance", "default"}
_ALLOWED_TASKS = {
    "src.pharmaviyum.ai.mortarium_rag.ingestion.tasks.ingest_document",
    "src.pharmaviyum.ai.mortarium_rag.ingestion.tasks.ingest_batch",
    "src.pharmaviyum.ai.mortarium_rag.ingestion.tasks.cleanup_old_jobs",
    "src.pharmaviyum.sync.worker.dispatch_outbox_batch",
    "other",
}


def _task_name(task) -> str:
    """Return an allow-listed task name for telemetry."""
    name = getattr(task, "name", "other")
    return name if name in _ALLOWED_TASKS else "other"


def _task_queue(task) -> str:
    """Return a bounded queue name for task telemetry."""
    route = (
        celery_app.conf.task_routes.get(task.name, {})
        if "celery_app" in globals()
        else {}
    )
    queue = route.get("queue") if isinstance(route, dict) else None
    return queue if queue in _ALLOWED_QUEUES else "default"


def _task_started(task_id: str, task) -> tuple[float, str, str]:
    queue = _task_queue(task)
    started = time.perf_counter()
    task_name = _task_name(task)
    with _TASK_START_LOCK:
        _TASK_START_TIMES[task_id] = (started, task_name, queue)
    CELERY_TASKS_IN_FLIGHT.labels(queue=queue).inc()
    return started, task_name, queue


def _task_finished(task_id: str, task, status: str) -> None:
    if task_id is None or task is None:
        return
    with _TASK_START_LOCK:
        started = _TASK_START_TIMES.pop(task_id, None)
    if started is None:
        return

    started_at, task_name, queue = started
    CELERY_TASK_DURATION.labels(task=task_name, queue=queue).observe(
        time.perf_counter() - started_at
    )
    CELERY_TASKS_IN_FLIGHT.labels(queue=queue).dec()
    CELERY_TASKS_TOTAL.labels(task=task_name, queue=queue, status=status).inc()


@signals.task_prerun.connect
def _task_prerun(task_id=None, task=None, **kwargs) -> None:
    if task is not None and task_id is not None:
        _task_started(task_id, task)


@signals.task_postrun.connect
def _task_postrun(task_id=None, task=None, state=None, **kwargs) -> None:
    _task_finished(task_id, task, str(state or "unknown").lower())


@signals.task_failure.connect
def _task_failure(task_id=None, task=None, **kwargs) -> None:
    # task_failure fires before task_postrun; the start entry is consumed here,
    # preventing a failed task from being counted twice.
    _task_finished(task_id, task, "failure")


def create_celery_app() -> Celery:
    """Create and configure Celery application."""
    app = Celery(
        "pharmaviyum.ai.ingestion",
        broker=settings.REDIS_URL,
        backend=settings.REDIS_URL,
        include=[
            "src.pharmaviyum.ai.mortarium_rag.ingestion.tasks",
            "src.pharmaviyum.sync.worker",
        ],
    )

    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=3600,
        task_soft_time_limit=3000,
        worker_max_tasks_per_child=100,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        result_expires=86400,
        result_extended=True,
        task_routes={
            "src.pharmaviyum.ai.mortarium_rag.ingestion.tasks.ingest_document": {
                "queue": "ingestion"
            },
            "src.pharmaviyum.ai.mortarium_rag.ingestion.tasks.ingest_batch": {
                "queue": "ingestion"
            },
            "src.pharmaviyum.ai.mortarium_rag.ingestion.tasks.cleanup_old_jobs": {
                "queue": "maintenance"
            },
            "src.pharmaviyum.sync.worker.dispatch_outbox_batch": {
                "queue": "maintenance"
            },
        },
        task_queue_max_priority=10,
        task_default_priority=5,
        worker_prefetch_multiplier=1,
        beat_schedule={
            "cleanup-old-ingestion-jobs": {
                "task": "src.pharmaviyum.ai.mortarium_rag.ingestion.tasks.cleanup_old_jobs",
                "schedule": 86400.0,
            },
            "dispatch-pharmacy-edge-outbox": {
                "task": "src.pharmaviyum.sync.worker.dispatch_outbox_batch",
                "schedule": 5.0,
                "options": {"expires": 10},
            },
        },
    )

    logger.info("Celery app configured for document ingestion")
    return app


celery_app = create_celery_app()
