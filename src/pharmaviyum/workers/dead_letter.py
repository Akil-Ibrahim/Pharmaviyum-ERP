"""
Dead letter queue for failed tasks
Best practice 2026: Never lose failed tasks, enable manual retry
"""
import json
from typing import Any, Optional
from datetime import datetime, timezone
from redis import asyncio as aioredis
from src.pharmaviyum.core.config import settings
from src.pharmaviyum.core.logging import get_logger
from src.pharmaviyum.workers.base import TaskResult

logger = get_logger(__name__)

DEAD_LETTER_TTL = 30 * 24 * 3600  # 30 days


class DeadLetterQueue:
    """
    Dead letter queue for storing failed tasks
    
    Features:
    - Stores failed task metadata
    - Enables manual inspection and retry
    - Automatic expiration (30 days)
    - Metrics and monitoring
    """
    
    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        """Initialize dead letter queue"""
        self.redis = redis_client or aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        self.queue_key = "dead_letter_queue"
        self.index_key = "dead_letter_index"
    
    async def add(
        self,
        task_name: str,
        task_args: dict[str, Any],
        result: TaskResult,
        original_queue: str,
    ) -> str:
        """
        Add failed task to dead letter queue
        
        Args:
            task_name: Name of the failed task
            task_args: Original task arguments
            result: Task result with error info
            original_queue: Queue the task was in
            
        Returns:
            Dead letter entry ID
        """
        import uuid
        
        entry_id = str(uuid.uuid4())
        
        entry = {
            "id": entry_id,
            "task_name": task_name,
            "task_args": task_args,
            "original_queue": original_queue,
            "error": result.error,
            "attempts": result.attempts,
            "duration_ms": result.duration_ms,
            "failed_at": datetime.now(timezone.utc).isoformat(),
            "status": "failed",  # failed/retrying/retried/discarded
        }
        
        # Store entry
        await self.redis.hset(
            self.index_key,
            entry_id,
            json.dumps(entry, ensure_ascii=False),
        )
        
        # Add to queue (sorted by timestamp for FIFO)
        await self.redis.zadd(
            self.queue_key,
            {entry_id: datetime.now(timezone.utc).timestamp()},
        )
        
        # Set TTL
        await self.redis.expire(self.queue_key, DEAD_LETTER_TTL)
        await self.redis.expire(self.index_key, DEAD_LETTER_TTL)
        
        logger.error(
            f"Task added to dead letter queue",
            extra={
                "entry_id": entry_id,
                "task_name": task_name,
                "error": result.error,
                "attempts": result.attempts,
            }
        )
        
        return entry_id
    
    async def list_entries(
        self,
        skip: int = 0,
        limit: int = 50,
        task_name: Optional[str] = None,
    ) -> list[dict]:
        """
        List dead letter entries
        
        Args:
            skip: Pagination offset
            limit: Pagination limit
            task_name: Filter by task name
            
        Returns:
            List of dead letter entries
        """
        # Get all entry IDs
        entry_ids = await self.redis.zrevrange(
            self.queue_key,
            skip,
            skip + limit - 1,
        )
        
        if not entry_ids:
            return []
        
        # Fetch entries
        entries = []
        for entry_id in entry_ids:
            entry_json = await self.redis.hget(self.index_key, entry_id)
            if entry_json:
                entry = json.loads(entry_json)
                
                # Apply filter
                if task_name and entry.get("task_name") != task_name:
                    continue
                
                entries.append(entry)
        
        return entries
    
    async def get_entry(self, entry_id: str) -> Optional[dict]:
        """Get specific dead letter entry"""
        entry_json = await self.redis.hget(self.index_key, entry_id)
        if entry_json:
            return json.loads(entry_json)
        return None
    
    async def mark_retried(self, entry_id: str) -> bool:
        """Mark entry as retried"""
        entry = await self.get_entry(entry_id)
        if not entry:
            return False
        
        entry["status"] = "retried"
        entry["retried_at"] = datetime.now(timezone.utc).isoformat()
        
        await self.redis.hset(
            self.index_key,
            entry_id,
            json.dumps(entry, ensure_ascii=False),
        )
        
        return True
    
    async def mark_discarded(self, entry_id: str) -> bool:
        """Mark entry as discarded"""
        entry = await self.get_entry(entry_id)
        if not entry:
            return False
        
        entry["status"] = "discarded"
        entry["discarded_at"] = datetime.now(timezone.utc).isoformat()
        
        await self.redis.hset(
            self.index_key,
            entry_id,
            json.dumps(entry, ensure_ascii=False),
        )
        
        return True
    
    async def delete_entry(self, entry_id: str) -> bool:
        """Delete entry from dead letter queue"""
        await self.redis.hdel(self.index_key, entry_id)
        await self.redis.zrem(self.queue_key, entry_id)
        return True
    
    async def count(self) -> int:
        """Count entries in dead letter queue"""
        return await self.redis.zcard(self.queue_key)
    
    async def clear_old(self, days: int = 7) -> int:
        """Clear entries older than N days"""
        cutoff = datetime.now(timezone.utc).timestamp() - (days * 24 * 3600)
        
        # Get old entries
        old_entries = await self.redis.zrangebyscore(
            self.queue_key,
            0,
            cutoff,
        )
        
        if not old_entries:
            return 0
        
        # Delete entries
        for entry_id in old_entries:
            await self.delete_entry(entry_id)
        
        logger.info(f"Cleared {len(old_entries)} old dead letter entries")
        return len(old_entries)


# Singleton instance
dead_letter_queue = DeadLetterQueue()
