"""Unit tests for atomic Redis task dispatch."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from src.pharmaviyum.workers.dispatcher import TaskDispatcher


@pytest.mark.asyncio
async def test_dispatch_uses_one_atomic_script_for_task_and_queue():
    redis = AsyncMock()
    redis.eval.return_value = 1
    dispatcher = TaskDispatcher(redis_client=redis)

    task_id = await dispatcher.dispatch(
        task_name="send_notification",
        task_args={"message": "hello"},
        queue="notifications",
        idempotency_key="notification:order:123",
        scheduled_at=datetime(2026, 11, 20, tzinfo=timezone.utc),
    )

    assert task_id == "notification:order:123"
    redis.eval.assert_awaited_once()
    args = redis.eval.await_args.args
    assert args[1] == 2
    assert args[2] == "task:notification:order:123"
    assert args[3] == "queue:notifications"
    assert args[4] == 86400
    assert '"task_id": "notification:order:123"' in args[5]
    assert args[6] == "notification:order:123"


@pytest.mark.asyncio
async def test_dispatch_returns_existing_idempotency_key_without_second_write():
    redis = AsyncMock()
    redis.eval.return_value = 0
    dispatcher = TaskDispatcher(redis_client=redis)

    task_id = await dispatcher.dispatch(
        task_name="send_notification",
        task_args={"message": "hello"},
        idempotency_key="notification:order:123",
    )

    assert task_id == "notification:order:123"
    redis.eval.assert_awaited_once()
    redis.setex.assert_not_awaited()
    redis.zadd.assert_not_awaited()


@pytest.mark.asyncio
async def test_dispatch_rejects_unsupported_queue_before_redis_write():
    redis = AsyncMock()
    dispatcher = TaskDispatcher(redis_client=redis)

    with pytest.raises(ValueError, match="Unsupported task queue"):
        await dispatcher.dispatch(
            task_name="send_notification",
            task_args={},
            queue="unknown",
        )

    redis.eval.assert_not_awaited()
