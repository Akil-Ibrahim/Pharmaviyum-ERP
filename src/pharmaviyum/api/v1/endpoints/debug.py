"""
Debug and diagnostic endpoints (admin only)
Best practice 2026: Safe diagnostic tools for production debugging
"""
import os
import sys
import platform
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from src.pharmaviyum.core.config import settings
from src.pharmaviyum.core.health import health_checker
from src.pharmaviyum.workers.dispatcher import task_dispatcher
from src.pharmaviyum.workers.dead_letter import dead_letter_queue

router = APIRouter(prefix="/debug", tags=["debug"])


# TODO: Add proper admin authentication
# For now, only available in development
def require_admin():
    """Require admin role (placeholder)"""
    if settings.ENVIRONMENT.value == "production":
        # TODO: Implement proper admin auth
        pass


@router.get("/info")
async def system_info():
    """
    System information endpoint
    
    Returns detailed system info for debugging.
    Admin only in production.
    """
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
            "total_mb": round(memory.total / (1024 ** 2), 2),
            "available_mb": round(memory.available / (1024 ** 2), 2),
            "used_percent": memory.percent,
        },
        "disk": {
            "total_gb": round(disk.total / (1024 ** 3), 2),
            "used_gb": round(disk.used / (1024 ** 3), 2),
            "free_gb": round(disk.free / (1024 ** 3), 2),
            "used_percent": disk.percent,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/config")
async def config_info():
    """
    Configuration endpoint (secrets masked)
    
    Returns current configuration with sensitive values masked.
    """
    # Get all settings, mask sensitive ones
    sensitive_keys = {"SECRET_KEY", "DATABASE_URL", "REDIS_URL", "KIOVIET_API_KEY", "SAPO_API_KEY"}
    
    config_dict = {}
    for key in dir(settings):
        if key.isupper() and not key.startswith("_"):
            value = getattr(settings, key)
            
            # Mask sensitive values
            if key in sensitive_keys and value:
                value = "***MASKED***"
            
            # Convert enums to strings
            if hasattr(value, "value"):
                value = value.value
            
            config_dict[key] = value
    
    return {
        "config": config_dict,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/queues")
async def queue_status():
    """
    Queue status endpoint
    
    Returns current state of all background job queues.
    """
    queue_lengths = await task_dispatcher.get_all_queue_lengths()
    dead_letter_count = await dead_letter_queue.count()
    
    return {
        "queues": queue_lengths,
        "dead_letter_count": dead_letter_count,
        "total_pending": sum(queue_lengths.values()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/detailed")
async def detailed_health():
    """
    Detailed health check endpoint
    
    Returns full health check results with all details.
    """
    health = await health_checker.check_all()
    return health.to_dict()


@router.post("/health/invalidate-cache")
async def invalidate_health_cache():
    """
    Invalidate health check cache
    
    Forces fresh health checks on next request.
    """
    health_checker.invalidate_cache()
    return {"status": "cache_invalidated"}


@router.get("/dead-letter")
async def list_dead_letter(
    skip: int = 0,
    limit: int = 50,
    task_name: str = None,
):
    """
    List dead letter queue entries
    
    Returns failed tasks for manual inspection.
    """
    entries = await dead_letter_queue.list_entries(
        skip=skip,
        limit=limit,
        task_name=task_name,
    )
    
    total = await dead_letter_queue.count()
    
    return {
        "entries": entries,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/dead-letter/{entry_id}/retry")
async def retry_dead_letter_entry(entry_id: str):
    """
    Retry a failed task from dead letter queue
    
    Re-queues the task for processing.
    """
    entry = await dead_letter_queue.get_entry(entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dead letter entry not found",
        )
    
    # Re-dispatch task
    await task_dispatcher.dispatch(
        task_name=entry["task_name"],
        task_args=entry["task_args"],
        queue=entry["original_queue"],
    )
    
    # Mark as retried
    await dead_letter_queue.mark_retried(entry_id)
    
    return {
        "status": "retried",
        "entry_id": entry_id,
        "task_name": entry["task_name"],
    }


@router.delete("/dead-letter/{entry_id}")
async def discard_dead_letter_entry(entry_id: str):
    """
    Discard a dead letter entry
    
    Marks the entry as discarded (won't be retried).
    """
    success = await dead_letter_queue.mark_discarded(entry_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dead letter entry not found",
        )
    
    return {"status": "discarded", "entry_id": entry_id}


@router.get("/cache/stats")
async def cache_stats():
    """
    Cache statistics endpoint
    
    Returns cache hit rates and sizes.
    """
    from redis import asyncio as aioredis
    
    redis = aioredis.from_url(settings.REDIS_URL)
    
    try:
        info = await redis.info("memory")
        keyspace = await redis.info("keyspace")
        db_size = await redis.dbsize()
        
        return {
            "memory": {
                "used_memory_human": info.get("used_memory_human"),
                "used_memory_peak_human": info.get("used_memory_peak_human"),
                "mem_fragmentation_ratio": info.get("mem_fragmentation_ratio"),
            },
            "keyspace": {
                "total_keys": db_size,
                "details": keyspace,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    finally:
        await redis.close()
