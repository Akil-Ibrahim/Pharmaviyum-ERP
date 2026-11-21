"""
Document Ingestion Module — Full RAG pipeline orchestration.

Public API:
- IngestionOrchestrator: Main entry point for ingestion
- DocumentDeduplicator: Prevent duplicate documents
- DocumentVersionManager: Manage document versions
- IngestionProgressTracker: Redis-based progress tracking
- Celery tasks: ingest_document, ingest_batch, cleanup_old_jobs
"""

from .celery_app import celery_app
from .deduplication import DedupStrategy, DocumentDeduplicator
from .orchestrator import IngestionOrchestrator
from .progress import IngestionProgressTracker, IngestionStatus
from .tasks import cleanup_old_jobs, ingest_batch, ingest_document
from .versioning import DocumentVersionManager, VersionStatus

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
