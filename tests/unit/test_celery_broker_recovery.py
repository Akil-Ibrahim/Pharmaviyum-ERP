"""Regression tests for bounded Celery broker recovery configuration."""

import pytest

from src.pharmaviyum.ai.mortarium_rag.ingestion.celery_app import create_celery_app
from src.pharmaviyum.core.config import Settings


def test_celery_broker_retries_are_enabled_and_bounded() -> None:
    settings = Settings(_env_file=None)
    app = create_celery_app()

    assert settings.CELERY_BROKER_CONNECTION_MAX_RETRIES == 12
    assert settings.CELERY_BROKER_RETRY_ON_STARTUP is True
    assert app.conf.broker_connection_retry is True
    assert app.conf.broker_connection_retry_on_startup is True
    assert app.conf.broker_connection_max_retries == 12


def test_celery_redis_transport_has_bounded_socket_timeouts() -> None:
    app = create_celery_app()

    assert app.conf.broker_connection_timeout == 5.0
    assert app.conf.broker_transport_options == {
        "socket_connect_timeout": 5.0,
        "socket_timeout": 5.0,
        "retry_on_timeout": True,
        "health_check_interval": 30,
        "max_retries": 12,
    }
    assert app.conf.result_backend_transport_options == {
        "socket_connect_timeout": 5.0,
        "socket_timeout": 5.0,
        "retry_on_timeout": True,
        "health_check_interval": 30,
    }


def test_celery_reduces_prefetch_after_broker_reconnect() -> None:
    app = create_celery_app()

    assert app.conf.worker_enable_prefetch_count_reduction is True
    assert app.conf.worker_prefetch_multiplier == 1
    assert app.conf.task_acks_late is True
    assert app.conf.task_reject_on_worker_lost is True


@pytest.mark.unit
def test_ingestion_task_raises_after_terminal_retry_exhaustion(monkeypatch) -> None:
    """A terminal ingestion error must remain a Celery FAILURE, not SUCCESS."""
    import asyncio
    from unittest.mock import AsyncMock, Mock

    from src.pharmaviyum.ai.mortarium_rag.ingestion import tasks as ingestion_tasks

    failure = RuntimeError("embedding provider unavailable")
    redis_client = object()
    tracker = Mock()
    tracker.update_status = AsyncMock()

    class Loop:
        def run_until_complete(self, awaitable):
            return asyncio.run(awaitable)

    loop = Loop()

    async def fail_ingestion(*args, **kwargs):
        raise failure

    monkeypatch.setattr(ingestion_tasks, "_ingest_document_async", fail_ingestion)
    monkeypatch.setattr(ingestion_tasks, "get_event_loop", lambda: loop)
    monkeypatch.setattr(
        ingestion_tasks, "get_redis", AsyncMock(return_value=redis_client)
    )
    monkeypatch.setattr(ingestion_tasks, "IngestionProgressTracker", lambda _: tracker)
    record_batch_result = Mock()
    monkeypatch.setattr(ingestion_tasks, "_record_batch_result", record_batch_result)

    config = {"pharmacy_id": 731, "batch_job_id": "batch-1"}
    task = ingestion_tasks.ingest_document
    task.push_request(retries=task.max_retries)
    try:
        with pytest.raises(RuntimeError, match="embedding provider unavailable"):
            task.run("tenant-source.pdf", "pdf", "child-1", config)
    finally:
        task.pop_request()

    tracker.update_status.assert_awaited_once_with(
        "child-1", "failed", error="Document ingestion failed"
    )
    record_batch_result.assert_called_once_with(loop, config, False, "child-1")
