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
from typing import Any, Awaitable, Literal, cast
from urllib.parse import urlsplit, urlunsplit

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

        await cast(
            Awaitable[bool],
            self.redis.setex(
                f"{self.prefix}:{job_id}", self.ttl_seconds, json.dumps(job_data)
            ),
        )

        logger.info(f"Ingestion job created: {job_id} ({total_documents} documents)")
        if total_documents > 0:
            await cast(
                Awaitable[int],
                self.redis.hset(
                    f"{self.prefix}:{job_id}:batch",
                    mapping={"total": total_documents, "processed": 0, "failed": 0},
                ),
            )
            await cast(
                Awaitable[int],
                self.redis.expire(f"{self.prefix}:{job_id}:batch", self.ttl_seconds),
            )

    async def record_batch_result(
        self,
        batch_job_id: str,
        child_job_id: str,
        success: bool,
    ) -> None:
        """Atomically deduplicate a child result and update its parent progress."""
        counters_key = f"{self.prefix}:{batch_job_id}:batch"
        marker_key = f"{self.prefix}:{batch_job_id}:child:{child_job_id}:counted"
        job_key = f"{self.prefix}:{batch_job_id}"
        field = "processed" if success else "failed"
        completed_at = datetime.utcnow().isoformat()

        # The marker, counters, and parent JSON must move together. A crash
        # between a separate SET NX and HINCRBY previously lost child results;
        # a retry then saw the marker and permanently skipped the increment.
        script = """
        local total = tonumber(redis.call("HGET", KEYS[2], "total") or "0")
        if total <= 0 then
            return {0, 0, 0, 0}
        end

        local created = redis.call(
            "SET", KEYS[1], "1", "EX", ARGV[1], "NX"
        )
        if created then
            redis.call("HINCRBY", KEYS[2], ARGV[2], 1)
        end

        local processed = tonumber(redis.call("HGET", KEYS[2], "processed") or "0")
        local failed = tonumber(redis.call("HGET", KEYS[2], "failed") or "0")
        local job_raw = redis.call("GET", KEYS[3])
        if job_raw then
            local job = cjson.decode(job_raw)
            local completed = processed + failed
            job["processed_documents"] = processed
            job["failed_documents"] = failed
            job["progress_percent"] = math.floor((processed / total) * 10000 + 0.5) / 100
            if completed >= total then
                job["status"] = failed == 0 and "completed" or "failed"
                job["current_step"] = "documents processed"
                job["completed_at"] = ARGV[3]
            else
                job["status"] = "queued"
                job["current_step"] = "processing documents"
            end
            redis.call("SETEX", KEYS[3], ARGV[1], cjson.encode(job))
        end
        redis.call("EXPIRE", KEYS[2], ARGV[1])
        return {created and 1 or 0, total, processed, failed}
        """

        await cast(
            Awaitable[list[Any]],
            self.redis.eval(
                script,
                3,
                marker_key,
                counters_key,
                job_key,
                self.ttl_seconds,
                field,
                completed_at,
            ),
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
        job_data_raw = await cast(Awaitable[Any], self.redis.get(key))

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
        await cast(
            Awaitable[bool],
            self.redis.setex(key, self.ttl_seconds, json.dumps(job_data)),
        )

        logger.debug(
            f"Job {job_id} updated: {status} ({job_data['progress_percent']}%)"
        )

    async def get_job(self, job_id: str) -> dict[str, Any] | None:
        """Retrieve job status."""
        key = f"{self.prefix}:{job_id}"
        job_data_raw = await cast(Awaitable[Any], self.redis.get(key))

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
            job_data_raw = await cast(Awaitable[Any], self.redis.get(key))
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
            job_data_raw = await cast(Awaitable[Any], self.redis.get(key))
            if job_data_raw:
                job_data = json.loads(job_data_raw)
                started_at_str = job_data.get("started_at")

                if started_at_str:
                    started_at = datetime.fromisoformat(started_at_str)
                    if started_at < cutoff:
                        await cast(Awaitable[int], self.redis.delete(key))
                        removed += 1

        logger.info(f"Cleaned up {removed} old ingestion jobs")
        return removed
