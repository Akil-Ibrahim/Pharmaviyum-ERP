"""
Background workers package
All async task processing for Pharmaviyum CRM
"""
from .dispatcher import task_dispatcher, TaskDispatcher
from .dead_letter import dead_letter_queue, DeadLetterQueue
from .worker import Worker, run_worker, TASK_REGISTRY
from .base import BaseTask, TaskResult, RetryConfig
from .queues import TaskQueue, QUEUE_PRIORITIES, QUEUE_CONFIGS

__all__ = [
    "task_dispatcher",
    "TaskDispatcher",
    "dead_letter_queue",
    "DeadLetterQueue",
    "Worker",
    "run_worker",
    "TASK_REGISTRY",
    "BaseTask",
    "TaskResult",
    "RetryConfig",
    "TaskQueue",
    "QUEUE_PRIORITIES",
    "QUEUE_CONFIGS",
]
