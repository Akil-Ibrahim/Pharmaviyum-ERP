"""
Queue definitions for different task types
Best practice 2026: Separate queues for different priorities
"""

from enum import Enum


class TaskQueue(str, Enum):
    """
    Task queue types

    Separation allows:
    - Independent scaling per queue
    - Priority-based processing
    - Isolation of critical tasks
    """

    # Critical queues (process first)
    CRITICAL = "critical"  # Security alerts, system health
    NOTIFICATIONS = "notifications"  # Patient notifications (Zalo/LINE/WhatsApp)

    # Business queues
    POS_SYNC = "pos_sync"  # KiotViet/Sapo/Viettel sync
    ORDERS = "orders"  # Order processing
    PRESCRIPTIONS = "prescriptions"  # Prescription processing

    # Low priority
    ANALYTICS = "analytics"  # Report generation
    CLEANUP = "cleanup"  # Data cleanup, cache invalidation

    # Dead letter queue (failed tasks)
    DEAD_LETTER = "dead_letter"


# Queue priorities (lower number = higher priority)
QUEUE_PRIORITIES = {
    TaskQueue.CRITICAL: 1,
    TaskQueue.NOTIFICATIONS: 2,
    TaskQueue.POS_SYNC: 3,
    TaskQueue.ORDERS: 4,
    TaskQueue.PRESCRIPTIONS: 5,
    TaskQueue.ANALYTICS: 7,
    TaskQueue.CLEANUP: 8,
    TaskQueue.DEAD_LETTER: 9,
}


# Queue-specific configurations
QUEUE_CONFIGS = {
    TaskQueue.CRITICAL: {
        "max_concurrent": 10,
        "timeout_seconds": 60,
        "max_retries": 5,
    },
    TaskQueue.NOTIFICATIONS: {
        "max_concurrent": 20,
        "timeout_seconds": 30,
        "max_retries": 3,
    },
    TaskQueue.POS_SYNC: {
        "max_concurrent": 5,
        "timeout_seconds": 300,
        "max_retries": 3,
    },
    TaskQueue.ANALYTICS: {
        "max_concurrent": 2,
        "timeout_seconds": 600,
        "max_retries": 1,
    },
}
