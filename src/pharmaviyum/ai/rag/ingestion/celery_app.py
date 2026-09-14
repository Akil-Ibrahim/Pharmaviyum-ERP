"""
Celery Application Configuration for Document Ingestion.

Best practice 2026:
- Redis as broker and result backend
- Task routing for different ingestion workloads
- Retry policies with exponential backoff
- Task priority queues for urgent documents
"""
from __future__ import annotations
from celery import Celery
from src.pharmaviyum.core.config import settings
from src.pharmaviyum.core.logging import logger


def create_celery_app() -> Celery:
    """Create and configure Celery application."""
    
    app = Celery(
        'pharmaviyum.ai.ingestion',
        broker=settings.REDIS_URL,
        backend=settings.REDIS_URL,
        include=[
            'src.pharmaviyum.ai.rag.ingestion.tasks',
        ]
    )
    
    # Celery configuration
    app.conf.update(
        # Serialization
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        
        # Timezone
        timezone='UTC',
        enable_utc=True,
        
        # Task execution
        task_track_started=True,
        task_time_limit=3600,  # 1 hour max per task
        task_soft_time_limit=3000,  # 50 min soft limit
        worker_max_tasks_per_child=100,  # Restart worker after 100 tasks (memory management)
        
        # Retry policies
        task_acks_late=True,  # Acknowledge after completion (not before)
        task_reject_on_worker_lost=True,
        
        # Result backend
        result_expires=86400,  # Keep results for 24 hours
        result_extended=True,
        
        # Task routing
        task_routes={
            'src.pharmaviyum.ai.rag.ingestion.tasks.ingest_document': {'queue': 'ingestion'},
            'src.pharmaviyum.ai.rag.ingestion.tasks.ingest_batch': {'queue': 'ingestion'},
            'src.pharmaviyum.ai.rag.ingestion.tasks.reindex_collection': {'queue': 'maintenance'},
        },
        
        # Priority queues
        task_queue_max_priority=10,
        task_default_priority=5,
        
        # Worker prefetch
        worker_prefetch_multiplier=1,  # Process one task at a time per worker
        
        # Beat scheduler (for periodic tasks)
        beat_schedule={
            'cleanup-old-ingestion-jobs': {
                'task': 'src.pharmaviyum.ai.rag.ingestion.tasks.cleanup_old_jobs',
                'schedule': 86400.0,  # Daily
            },
        },
    )
    
    logger.info("Celery app configured for document ingestion")
    return app


# Global Celery app instance
celery_app = create_celery_app()
