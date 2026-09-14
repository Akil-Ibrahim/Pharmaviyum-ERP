"""
Document Ingestion Module — Full RAG pipeline orchestration.

Public API:
- IngestionOrchestrator: Main entry point for ingestion
- DocumentDeduplicator: Prevent duplicate documents
- DocumentVersionManager: Manage document versions
- IngestionProgressTracker: Redis-based progress tracking
- Celery tasks: ingest_document, ingest_batch, cleanup_old_jobs
"""
from .orchestrator import IngestionOrchestrator
from .deduplication import DocumentDeduplicator, DedupStrategy
from .versioning import DocumentVersionManager, VersionStatus
from .progress import IngestionProgressTracker, IngestionStatus
from .celery_app import celery_app
from .tasks import ingest_document, ingest_batch, cleanup_old_jobs

__all__ = [
    "IngestionOrchestrator",
    "DocumentDeduplicator",
    "DedupStrategy",
    "DocumentVersionManager",
    "VersionStatus",
    "IngestionProgressTracker",
    "IngestionStatus",
    "celery_app",
    "ingest_document",
    "ingest_batch",
    "cleanup_old_jobs",
]
