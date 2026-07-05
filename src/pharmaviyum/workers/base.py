"""
Base task infrastructure for background jobs
Best practice 2026: Retry logic, dead letter queue, observability
"""
import asyncio
from typing import Any, Callable, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field
from src.pharmaviyum.core.logging import get_logger
from src.pharmaviyum.core.config import settings

logger = get_logger(__name__)


@dataclass
class TaskResult:
    """Result of a task execution"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    attempts: int = 1
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class RetryConfig:
    """Configuration for task retry behavior"""
    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt with exponential backoff"""
        import random
        
        delay = min(
            self.base_delay_seconds * (self.exponential_base ** (attempt - 1)),
            self.max_delay_seconds,
        )
        
        if self.jitter:
            # Add jitter to prevent thundering herd
            delay = delay * (0.5 + random.random())
        
        return delay


class BaseTask:
    """
    Base class for all background tasks
    
    Features:
    - Automatic retry with exponential backoff
    - Dead letter queue for failed tasks
    - Structured logging
    - Metrics collection
    - Graceful shutdown support
    """
    
    # Task metadata (override in subclasses)
    name: str = "base_task"
    queue: str = "default"
    timeout_seconds: int = 300
    retry_config: RetryConfig = RetryConfig()
    
    def __init__(self):
        """Initialize task"""
        self._shutdown_event = asyncio.Event()
    
    async def execute(self, **kwargs) -> Any:
        """
        Execute task logic (override in subclasses)
        
        Args:
            **kwargs: Task arguments
            
        Returns:
            Task result data
        """
        raise NotImplementedError("Subclasses must implement execute()")
    
    async def run_with_retry(self, **kwargs) -> TaskResult:
        """
        Run task with retry logic
        
        Args:
            **kwargs: Task arguments
            
        Returns:
            TaskResult with success/failure info
        """
        start_time = datetime.now(timezone.utc)
        last_error = None
        
        for attempt in range(1, self.retry_config.max_attempts + 1):
            try:
                # Check for shutdown
                if self._shutdown_event.is_set():
                    logger.warning(
                        f"Task {self.name} interrupted by shutdown",
                        extra={"attempt": attempt}
                    )
                    return TaskResult(
                        success=False,
                        error="Task interrupted by shutdown",
                        attempts=attempt,
                    )
                
                logger.info(
                    f"Executing task {self.name}",
                    extra={
                        "attempt": attempt,
                        "max_attempts": self.retry_config.max_attempts,
                        "queue": self.queue,
                    }
                )
                
                # Execute task with timeout
                result = await asyncio.wait_for(
                    self.execute(**kwargs),
                    timeout=self.timeout_seconds,
                )
                
                duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                
                logger.info(
                    f"Task {self.name} completed successfully",
                    extra={
                        "duration_ms": round(duration_ms, 2),
                        "attempts": attempt,
                    }
                )
                
                return TaskResult(
                    success=True,
                    data=result,
                    duration_ms=duration_ms,
                    attempts=attempt,
                )
                
            except asyncio.TimeoutError:
                last_error = f"Task timed out after {self.timeout_seconds}s"
                logger.error(
                    f"Task {self.name} timeout",
                    extra={"attempt": attempt, "timeout": self.timeout_seconds}
                )
                
            except Exception as e:
                last_error = str(e)
                logger.error(
                    f"Task {self.name} failed",
                    extra={
                        "attempt": attempt,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                    exc_info=True,
                )
            
            # Wait before retry (if not last attempt)
            if attempt < self.retry_config.max_attempts:
                delay = self.retry_config.get_delay(attempt)
                logger.info(
                    f"Retrying task {self.name} in {delay:.2f}s",
                    extra={"attempt": attempt, "delay": delay}
                )
                await asyncio.sleep(delay)
        
        # All attempts failed
        duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        
        logger.error(
            f"Task {self.name} failed after {self.retry_config.max_attempts} attempts",
            extra={
                "duration_ms": round(duration_ms, 2),
                "last_error": last_error,
            }
        )
        
        return TaskResult(
            success=False,
            error=last_error,
            duration_ms=duration_ms,
            attempts=self.retry_config.max_attempts,
        )
    
    def request_shutdown(self):
        """Request graceful shutdown"""
        self._shutdown_event.set()
