"""
Celery tasks for tenant-scoped document ingestion.

Best practice 2026:
- tenant identity is required at the worker boundary
- source documents are stamped before chunking
- vector persistence remains fail-closed on canonical metadata
- async task execution with progress tracking and retry logic
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from typing import Any

from celery.utils.log import get_task_logger

from src.pharmaviyum.ai.mortarium_rag.chunking import MedicalChunker
from src.pharmaviyum.ai.mortarium_rag.embeddings import EmbeddingsFactory
from src.pharmaviyum.ai.mortarium_rag.loaders import (
    DOCXLoader,
    HTMLLoader,
    LoaderConfig,
    PDFLoader,
)
from src.pharmaviyum.ai.mortarium_rag.preprocessing import DocumentPreprocessor
from src.pharmaviyum.ai.mortarium_rag.vector_store import PgVectorStore
from src.pharmaviyum.core.database import async_session_factory
from src.pharmaviyum.redis_client import get_redis
from src.pharmaviyum.storage.object_storage import ObjectStorage

from .celery_app import celery_app
from .progress import IngestionProgressTracker

logger = get_task_logger(__name__)


def get_event_loop():
    """Get or create event loop for async operations in Celery."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


def _require_pharmacy_id(config: dict[str, Any]) -> int:
    """Require an already-authorized pharmacy tenant in worker input."""
    pharmacy_id = config.get("pharmacy_id")
    if (
        not isinstance(pharmacy_id, int)
        or isinstance(pharmacy_id, bool)
        or pharmacy_id <= 0
    ):
        raise ValueError(
            "Ingestion requires an authorized positive integer pharmacy_id"
        )
    return pharmacy_id


def _stamp_tenant_metadata(documents: list, config: dict[str, Any]) -> list:
    """Stamp tenant and canonical source metadata before chunking."""
    pharmacy_id = _require_pharmacy_id(config)
    country = config.get("country", "VN")
    language = config.get("language", "vi")
    access_level = config.get("access_level", "pharmacy")
    version = config.get("version")
    effective_from = config.get("effective_from")
    effective_to = config.get("effective_to")

    stamped = []
    for document in documents:
        metadata = {
            **document.metadata,
            "pharmacy_id": pharmacy_id,
            "source": document.source,
            "version": version,
            "effective_from": effective_from,
            "effective_to": effective_to,
            "access_level": access_level,
            "country": country,
            "language": language,
            "doc_type": document.doc_type,
        }
        stamped.append(
            document.model_copy(
                update={
                    "country": country,
                    "language": language,
                    "metadata": metadata,
                }
            )
        )
    return stamped


async def _ingest_document_async(
    source: str,
    source_type: str,
    job_id: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Async implementation of tenant-scoped document ingestion."""
    _require_pharmacy_id(config)

    redis_client = await get_redis()
    tracker = IngestionProgressTracker(redis_client)

    try:
        await tracker.update_status(job_id, "loading", "Loading document")
        local_source = source
        temp_path: str | None = None
        if config.get("source_storage") == "object":
            storage = ObjectStorage()
            payload = await storage.get_bytes(source)
            suffix = f".{source_type}" if source_type in {"pdf", "docx", "html"} else ""
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(payload)
                temp_path = tmp_file.name
            local_source = temp_path

        loader_config = LoaderConfig(
            source_type=source_type,
            batch_size=config.get("batch_size", 10),
            extract_tables=config.get("extract_tables", True),
            ocr_enabled=config.get("ocr_enabled", True),
            languages=config.get("languages", ["vi", "en", "ar", "th", "id"]),
            metadata_filters=config.get("metadata_filters", {}),
        )

        if source_type == "pdf":
            loader = PDFLoader()
        elif source_type == "html":
            loader = HTMLLoader()
        elif source_type == "docx":
            loader = DOCXLoader()
        else:
            raise ValueError(f"Unsupported source type: {source_type}")

        documents = []
        async for doc in loader.load(local_source, loader_config):
            documents.append(doc)
        if not documents:
            raise ValueError(f"No documents loaded from {source}")

        await tracker.update_status(job_id, "preprocessing", "Preprocessing documents")
        preprocessor = DocumentPreprocessor(
            enable_pii_redaction=config.get("redact_pii", True)
        )
        processed_docs = [preprocessor.process(doc) for doc in documents]
        processed_docs = _stamp_tenant_metadata(processed_docs, config)

        await tracker.update_status(job_id, "chunking", "Chunking documents")
        chunker = MedicalChunker(
            max_tokens=config.get("max_chunk_tokens", 512),
            overlap=config.get("chunk_overlap", 50),
        )
        all_chunks = []
        for doc in processed_docs:
            all_chunks.extend(
                chunker.chunk(doc, strategy=config.get("chunking_strategy", "medical"))
            )

        await tracker.update_status(job_id, "embedding", "Generating embeddings")
        embeddings_provider = EmbeddingsFactory.create(
            provider=config.get("embeddings_provider", "ollama"),
            use_cache=True,
            redis_client=redis_client,
        )
        embeddings = await embeddings_provider.embed_batch(
            [chunk.content for chunk in all_chunks],
            batch_size=config.get("embedding_batch_size", 32),
        )

        await tracker.update_status(job_id, "storing", "Storing in vector database")
        async with async_session_factory() as session:
            vector_store = PgVectorStore(
                session_factory=lambda: session,
                dimensions=embeddings_provider.dimensions,
            )
            await vector_store.initialize()
            await vector_store.upsert(all_chunks, embeddings)

        if config.get("source_storage") == "object":
            try:
                await ObjectStorage().delete(source)
            except Exception:
                # Keep the object for retry/recovery if cleanup fails.
                logger.exception("Failed to delete completed ingestion object %s", source)

        await tracker.update_status(job_id, "completed", processed=len(all_chunks))
        return {
            "success": True,
            "documents_loaded": len(documents),
            "chunks_created": len(all_chunks),
            "source": source,
        }

    finally:
        if temp_path:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="src.pharmaviyum.ai.mortarium_rag.ingestion.tasks.ingest_document",
)
def ingest_document(
    self,
    source: str,
    source_type: str,
    job_id: str,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Celery task for one tenant-scoped document."""
    config = config or {}
    logger.info("Starting ingestion task %s", job_id)
    try:
        loop = get_event_loop()
        return loop.run_until_complete(
            _ingest_document_async(source, source_type, job_id, config)
        )
    except Exception as exc:
        logger.error("Task failed: %s", exc, exc_info=True)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        try:
            loop = get_event_loop()
            redis_client = loop.run_until_complete(get_redis())
            tracker = IngestionProgressTracker(redis_client)
            loop.run_until_complete(
                tracker.update_status(job_id, "failed", error=str(exc))
            )
        except Exception:
            logger.exception("Failed to mark ingestion job %s as failed", job_id)
        return {"success": False, "error": str(exc), "source": source}


@celery_app.task(
    bind=True,
    name="src.pharmaviyum.ai.mortarium_rag.ingestion.tasks.ingest_batch",
)
def ingest_batch(
    self,
    sources: list[dict[str, str]],
    job_id: str,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Queue multiple tenant-scoped ingestion tasks."""
    config = config or {}
    _require_pharmacy_id(config)
    redis_client = None
    try:
        loop = get_event_loop()
        redis_client = loop.run_until_complete(get_redis())
        tracker = IngestionProgressTracker(redis_client)
        loop.run_until_complete(
            tracker.create_job(job_id, f"batch_{len(sources)}", len(sources), config)
        )

        results = []
        failed = 0
        for index, source_info in enumerate(sources):
            source = source_info["source"]
            source_type = source_info["source_type"]
            try:
                task = ingest_document.delay(
                    source, source_type, f"{job_id}_doc_{index}", config
                )
                results.append(
                    {"source": source, "task_id": task.id, "status": "queued"}
                )
            except Exception as exc:
                failed += 1
                results.append(
                    {"source": source, "status": "failed", "error": str(exc)}
                )

        loop.run_until_complete(
            tracker.update_status(
                job_id,
                "queued",
                current_step="documents queued",
                processed=0,
                failed=failed,
            )
        )
        return {
            "success": True,
            "total_documents": len(sources),
            "queued": len(sources) - failed,
            "failed_to_queue": failed,
            "results": results,
        }
    finally:
        # The shared client is process-owned and must not be closed per task.
        pass


@celery_app.task(
    name="src.pharmaviyum.ai.mortarium_rag.ingestion.tasks.cleanup_old_jobs"
)
def cleanup_old_jobs() -> dict[str, Any]:
    """Periodic task: clean old ingestion jobs from Redis."""
    loop = get_event_loop()
    redis_client = loop.run_until_complete(get_redis())
    tracker = IngestionProgressTracker(redis_client)
    removed = loop.run_until_complete(tracker.cleanup_old_jobs(days_old=7))
    return {"removed_jobs": removed}
