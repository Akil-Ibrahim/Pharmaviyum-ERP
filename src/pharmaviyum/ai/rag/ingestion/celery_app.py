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
from collections.abc import MutableMapping
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


# Queue names are intentionally allow-listed. Never derive metric labels from
# arbitrary broker routing input or task arguments.
_TASK_QUEUES = {
    "src.pharmaviyum.ai.rag.ingestion.tasks.ingest_document": "ingestion",
    "src.pharmaviyum.ai.rag.ingestion.tasks.ingest_batch": "ingestion",
    "src.pharmaviyum.ai.rag.ingestion.tasks.reindex_collection": "maintenance",
    "src.pharmaviyum.ai.rag.ingestion.tasks.cleanup_old_jobs": "maintenance",
}


def _task_queue(task) -> str:
    """Return a bounded queue name for task telemetry."""
    route = celery_app.conf.task_routes.get(task.name, {}) if "celery_app" in globals() else {}
    queue = route.get("queue") if isinstance(route, MutableMapping) else None
    return queue if queue in {"ingestion", "maintenance"} else "default"


def _record_start(task_id: str, task) -> None:
    queue = _task_queue(task)
    with _TASK_START_LOCK:
        _TASK_START_TIMES[task_id] = (time.perf_counter(), task.name, queue)
    CELERY_TASKS_IN_FLIGHT.labels(queue=queue).inc()


@signals.task_prerun.connect
def _task_prerun(task_id=None, task=None, **kwargs) -> None:
    if task is not None and task_id is not None:
        _record_start(task_id, task)


@signals.task_postrun.connect
@signals.task_failure.connect
def _task_finished(task_id=None, task=None, **kwargs) -> None:
    if task is None or task_id is None:
        return

    with _TASK_START_LOCK:
        started = _TASK_START_TIMES.pop(task_id, None)

    if started is None:
        return

    started_at, task_name, queue = started
    duration = time.perf_counter() - started_at
    CELERY_TASK_DURATION.labels(task=task_name, queue=queue).observe(duration)
    CELERY_TASKS_IN_FLIGHT.labels(queue=queue).dec()

    # task_failure does not provide a Celery task state argument consistently;
    # use the signal name so failure accounting cannot silently become success.
    signal_name = kwargs.get("state") or "failure" if "exception" in kwargs else kwargs.get("state", "unknown")
    status = str(signal_name).lower()
    if status not in {"success", "failure", "retry", "revoked", "started", "unknown"}:
        status = "unknown"
    CELERY_TASKS_TOTAL.labels(task=task_name, queue=queue, status=status).inc()


def create_celery_app() -> Celery:
    """Create and configure Celery application."""
    app = Celery(
        "pharmaviyum.ai.ingestion",
        broker=settings.REDIS_URL,
        backend=settings.REDIS_URL,
        include=["src.pharmaviyum.ai.rag.ingestion.tasks"],
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
            "src.pharmaviyum.ai.rag.ingestion.tasks.ingest_document": {"queue": "ingestion"},
            "src.pharmaviyum.ai.rag.ingestion.tasks.ingest_batch": {"queue": "ingestion"},
            "src.pharmaviyum.ai.rag.ingestion.tasks.reindex_collection": {"queue": "maintenance"},
            "src.pharmaviyum.ai.rag.ingestion.tasks.cleanup_old_jobs": {"queue": "maintenance"},
        },
        task_queue_max_priority=10,
        task_default_priority=5,
        worker_prefetch_multiplier=1,
        beat_schedule={
            "cleanup-old-ingestion-jobs": {
                "task": "src.pharmaviyum.ai.rag.ingestion.tasks.cleanup_old_jobs",
                "schedule": 86400.0,
            },
        },
    )

    logger.info("Celery app configured for document ingestion")
    return app


celery_app = create_celery_app()
