"""
Ingestion Progress Tracking via Redis.

Best practice 2026:
- Real-time progress updates for long-running ingestion
- Structured status for API polling
- Automatic cleanup of old jobs
"""

from __future__ import annotations

import json
from urllib.parse import urlsplit, urlunsplit
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

    @staticmethod
    def _safe_source(source: str) -> str:
        """Redact URL credentials and query/fragment secrets before persistence."""
        try:
            parsed = urlsplit(source)
        except ValueError:
            return "<redacted>"
        if parsed.scheme in {"http", "https"} and parsed.hostname:
            netloc = parsed.hostname
            if parsed.port:
                netloc = f"{netloc}:{parsed.port}"
            return urlunsplit((parsed.scheme, netloc, parsed.path, "", ""))
        return source

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
            "source": self._safe_source(source),
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
        if total_documents > 0:
            await self.redis.hset(
                f"{self.prefix}:{job_id}:batch",
                mapping={"total": total_documents, "processed": 0, "failed": 0},
            )
            await self.redis.expire(f"{self.prefix}:{job_id}:batch", self.ttl_seconds)

    async def record_batch_result(self, batch_job_id: str, success: bool) -> None:
        """Record one child result and finalize its parent without lost updates."""
        lock = self.redis.lock(
            f"{self.prefix}:{batch_job_id}:batch:lock",
            timeout=30,
            blocking_timeout=10,
        )
        async with lock:
            counters_key = f"{self.prefix}:{batch_job_id}:batch"
            field = "processed" if success else "failed"
            await self.redis.hincrby(counters_key, field, 1)
            total_raw = await self.redis.hget(counters_key, "total")
            if not total_raw:
                return
            total = int(total_raw)
            failed_raw = await self.redis.hget(counters_key, "failed")
            failed = int(failed_raw or 0)
            processed_raw = await self.redis.hget(counters_key, "processed")
            processed = int(processed_raw or 0)
            completed = processed + failed
            if completed >= total:
                await self.update_status(
                    batch_job_id,
                    "completed" if failed == 0 else "failed",
                    current_step="documents processed",
                    processed=processed,
                    failed=failed,
                )
            else:
                await self.update_status(
                    batch_job_id,
                    "queued",
                    current_step="processing documents",
                    processed=processed,
                    failed=failed,
                )

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
            key_text = key.decode() if isinstance(key, bytes) else key
            if key_text.endswith(":batch"):
                continue
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
            key_text = key.decode() if isinstance(key, bytes) else key
            if key_text.endswith(":batch"):
                continue
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
