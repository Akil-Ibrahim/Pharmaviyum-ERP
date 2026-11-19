"""Regression tests for bounded Celery broker recovery configuration."""

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
