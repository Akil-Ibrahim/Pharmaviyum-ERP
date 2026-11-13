"""Celery task entry point for the durable Edge outbox dispatcher."""

from src.pharmaviyum.ai.mortarium_rag.ingestion.celery_app import celery_app
from src.pharmaviyum.services.outbox_dispatcher import run_outbox_dispatcher


@celery_app.task(
    name="src.pharmaviyum.sync.worker.dispatch_outbox_batch",
    ignore_result=True,
)
def dispatch_outbox_batch() -> int:
    """Attempt one bounded outbox delivery batch for this configured Edge node."""
    return run_outbox_dispatcher()
