"""
Ingestion Progress Tracking via Redis.

Best practice 2026:
- Real-time progress updates for long-running ingestion
- Structured status for API polling
- Automatic cleanup of old jobs
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Literal

from redis.asyncio import Redis

from src.pharmaviyum.core.logging import logger

IngestionStatus = Literal[
    "pending",
    "queued",
    "loading",
    "preprocessing",
    "chunking",
    "embedding",
    "storing",
    "completed",
    "failed",
]


class IngestionProgressTracker:
    """Track ingestion job progress in Redis."""

    def __init__(self, redis_client: Redis, ttl_hours: int = 24):
        self.redis = redis_client
        self.ttl_seconds = ttl_hours * 3600
        self.prefix = "ingestion:job"

    async def create_job(
        self,
        job_id: str,
        source: str,
        total_documents: int,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a new ingestion job."""
        job_data = {
            "job_id": job_id,
            "source": source,
            "status": "pending",
            "total_documents": total_documents,
            "processed_documents": 0,
            "failed_documents": 0,
            "current_step": "initializing",
            "progress_percent": 0.0,
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "errors": [],
            "metadata": metadata or {},
        }

        await self.redis.setex(
            f"{self.prefix}:{job_id}", self.ttl_seconds, json.dumps(job_data)
        )

        logger.info(f"Ingestion job created: {job_id} ({total_documents} documents)")

    async def update_status(
        self,
        job_id: str,
        status: IngestionStatus,
        current_step: str | None = None,
        processed: int | None = None,
        failed: int | None = None,
        error: str | None = None,
    ) -> None:
        """Update job status and progress."""
        key = f"{self.prefix}:{job_id}"
        job_data_raw = await self.redis.get(key)

        if not job_data_raw:
            logger.warning(f"Job {job_id} not found")
            return

        job_data = json.loads(job_data_raw)

        # Update fields
        job_data["status"] = status
        if current_step:
            job_data["current_step"] = current_step
        if processed is not None:
            job_data["processed_documents"] = processed
        if failed is not None:
            job_data["failed_documents"] = failed
        if error:
            job_data["errors"].append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": error,
                }
            )

        # Calculate progress
        total = job_data["total_documents"]
        processed_count = job_data["processed_documents"]
        if total > 0:
            job_data["progress_percent"] = round((processed_count / total) * 100, 2)

        # Mark completion
        if status in ["completed", "failed"]:
            job_data["completed_at"] = datetime.utcnow().isoformat()

        # Save back to Redis
        await self.redis.setex(key, self.ttl_seconds, json.dumps(job_data))

        logger.debug(
            f"Job {job_id} updated: {status} ({job_data['progress_percent']}%)"
        )

    async def get_job(self, job_id: str) -> dict[str, Any] | None:
        """Retrieve job status."""
        key = f"{self.prefix}:{job_id}"
        job_data_raw = await self.redis.get(key)

        if not job_data_raw:
            return None

        return json.loads(job_data_raw)

    async def list_jobs(
        self,
        status: IngestionStatus | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List recent ingestion jobs."""
        pattern = f"{self.prefix}:*"
        jobs = []

        async for key in self.redis.scan_iter(match=pattern, count=100):
            job_data_raw = await self.redis.get(key)
            if job_data_raw:
                job_data = json.loads(job_data_raw)

                # Filter by status if specified
                if status and job_data.get("status") != status:
                    continue

                jobs.append(job_data)

                if len(jobs) >= limit:
                    break

        # Sort by started_at (most recent first)
        jobs.sort(key=lambda x: x.get("started_at", ""), reverse=True)
        return jobs

    async def cleanup_old_jobs(self, days_old: int = 7) -> int:
        """Remove jobs older than specified days."""
        cutoff = datetime.utcnow() - timedelta(days=days_old)
        pattern = f"{self.prefix}:*"
        removed = 0

        async for key in self.redis.scan_iter(match=pattern, count=100):
            job_data_raw = await self.redis.get(key)
            if job_data_raw:
                job_data = json.loads(job_data_raw)
                started_at_str = job_data.get("started_at")

                if started_at_str:
                    started_at = datetime.fromisoformat(started_at_str)
                    if started_at < cutoff:
                        await self.redis.delete(key)
                        removed += 1

        logger.info(f"Cleaned up {removed} old ingestion jobs")
        return removed
