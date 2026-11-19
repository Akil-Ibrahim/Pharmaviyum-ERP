"""Integration tests for idempotent ingestion batch progress accounting."""

import asyncio
from uuid import uuid4

import pytest
from redis.asyncio import Redis

from src.pharmaviyum.ai.mortarium_rag.ingestion.progress import (
    IngestionProgressTracker,
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_batch_child_results_are_atomic_and_idempotent(
    test_redis: Redis,
) -> None:
    """Concurrent redelivery counts each child once and keeps parent totals exact."""
    batch_job_id = f"batch-{uuid4()}"
    tracker = IngestionProgressTracker(test_redis)
    await tracker.create_job(
        batch_job_id,
        source="batch_2",
        total_documents=2,
    )

    await asyncio.gather(
        tracker.record_batch_result(batch_job_id, "child-1", True),
        tracker.record_batch_result(batch_job_id, "child-1", True),
        tracker.record_batch_result(batch_job_id, "child-2", False),
    )

    counters = await test_redis.hgetall(f"ingestion:job:{batch_job_id}:batch")
    job = await tracker.get_job(batch_job_id)

    assert counters == {"total": "2", "processed": "1", "failed": "1"}
    assert job is not None
    assert job["status"] == "failed"
    assert job["processed_documents"] == 1
    assert job["failed_documents"] == 1
    assert job["progress_percent"] == 50.0
    assert job["completed_at"] is not None

    # A late duplicate after completion must not increment counters or regress
    # the terminal parent status.
    await tracker.record_batch_result(batch_job_id, "child-1", True)
    assert await test_redis.hgetall(
        f"ingestion:job:{batch_job_id}:batch"
    ) == counters
    final_job = await tracker.get_job(batch_job_id)
    assert final_job is not None
    assert final_job["status"] == "failed"
    assert final_job["processed_documents"] == 1
