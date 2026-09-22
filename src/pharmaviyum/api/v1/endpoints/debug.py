"""Debug and diagnostic endpoints (admin only)."""

import os
import platform
import sys
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from src.pharmaviyum.core.config import settings
from src.pharmaviyum.core.health import health_checker
from src.pharmaviyum.modules.auth.deps import CurrentSuperuser
from src.pharmaviyum.redis_client import get_redis
from src.pharmaviyum.workers.dead_letter import dead_letter_queue
from src.pharmaviyum.workers.dispatcher import task_dispatcher

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/info")
async def system_info(_: CurrentSuperuser):
    import psutil

    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    cpu_percent = psutil.cpu_percent(interval=0.1)
    return {
        "application": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT.value,
            "debug": settings.DEBUG,
        },
        "python": {
            "version": sys.version,
            "implementation": platform.python_implementation(),
            "path": sys.executable,
        },
        "system": {
            "platform": platform.platform(),
            "hostname": platform.node(),
            "cpu_count": os.cpu_count(),
            "cpu_percent": cpu_percent,
        },
        "memory": {
            "total_mb": round(memory.total / (1024**2), 2),
            "available_mb": round(memory.available / (1024**2), 2),
            "used_percent": memory.percent,
        },
        "disk": {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "used_percent": disk.percent,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/config")
async def config_info(_: CurrentSuperuser):
    sensitive_keys = {
        "SECRET_KEY",
        "DATABASE_URL",
        "REDIS_URL",
        "KIOVIET_API_KEY",
        "SAPO_API_KEY",
    }
    config_dict = {}
    for key in dir(settings):
        if key.isupper() and not key.startswith("_"):
            value = getattr(settings, key)
            if key in sensitive_keys and value:
                value = "***MASKED***"
            if hasattr(value, "value"):
                value = value.value
            config_dict[key] = value
    return {"config": config_dict, "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/queues")
async def queue_status(_: CurrentSuperuser):
    queue_lengths = await task_dispatcher.get_all_queue_lengths()
    dead_letter_count = await dead_letter_queue.count()
    return {
        "queues": queue_lengths,
        "dead_letter_count": dead_letter_count,
        "total_pending": sum(queue_lengths.values()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/detailed")
async def detailed_health(_: CurrentSuperuser):
    return (await health_checker.check_all()).to_dict()


@router.post("/health/invalidate-cache")
async def invalidate_health_cache(_: CurrentSuperuser):
    health_checker.invalidate_cache()
    return {"status": "cache_invalidated"}


@router.get("/dead-letter")
async def list_dead_letter(
    _: CurrentSuperuser, skip: int = 0, limit: int = 50, task_name: str = None
):
    entries = await dead_letter_queue.list_entries(
        skip=skip, limit=limit, task_name=task_name
    )
    total = await dead_letter_queue.count()
    return {"entries": entries, "total": total, "skip": skip, "limit": limit}


@router.post("/dead-letter/{entry_id}/retry")
async def retry_dead_letter_entry(_: CurrentSuperuser, entry_id: str):
    entry = await dead_letter_queue.get_entry(entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dead letter entry not found"
        )
    await task_dispatcher.dispatch(
        task_name=entry["task_name"],
        task_args=entry["task_args"],
        queue=entry["original_queue"],
    )
    await dead_letter_queue.mark_retried(entry_id)
    return {"status": "retried", "entry_id": entry_id, "task_name": entry["task_name"]}


@router.delete("/dead-letter/{entry_id}")
async def discard_dead_letter_entry(_: CurrentSuperuser, entry_id: str):
    success = await dead_letter_queue.mark_discarded(entry_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dead letter entry not found"
        )
    return {"status": "discarded", "entry_id": entry_id}


@router.get("/cache/stats")
async def cache_stats(_: CurrentSuperuser):
    redis = await get_redis()
    info = await redis.info("memory")
    keyspace = await redis.info("keyspace")
    db_size = await redis.dbsize()
    return {
        "memory": {
            "used_memory_human": info.get("used_memory_human"),
            "used_memory_peak_human": info.get("used_memory_peak_human"),
            "mem_fragmentation_ratio": info.get("mem_fragmentation_ratio"),
        },
        "keyspace": {"total_keys": db_size, "details": keyspace},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
