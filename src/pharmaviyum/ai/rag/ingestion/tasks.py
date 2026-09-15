"""
Celery Tasks for Document Ingestion.

Best practice 2026:
- Async task execution with progress tracking
- Batch processing for efficiency
- Retry logic with exponential backoff
- Error isolation (one failed document doesn't fail the batch)
"""

from __future__ import annotations

import asyncio
from typing import Any

from celery.utils.log import get_task_logger

from src.pharmaviyum.ai.rag.chunking import MedicalChunker
from src.pharmaviyum.ai.rag.embeddings import EmbeddingsFactory
from src.pharmaviyum.ai.rag.loaders import (DOCXLoader, HTMLLoader,
                                            LoaderConfig, PDFLoader)
from src.pharmaviyum.ai.rag.preprocessing import DocumentPreprocessor
from src.pharmaviyum.ai.rag.vector_store import PgVectorStore
from src.pharmaviyum.core.config import settings
from src.pharmaviyum.core.database import async_session_factory

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


async def _ingest_document_async(
    source: str,
    source_type: str,
    job_id: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Async implementation of document ingestion."""

    # Initialize Redis client for progress tracking
    import redis.asyncio as aioredis

    redis_client = aioredis.from_url(settings.REDIS_URL)
    tracker = IngestionProgressTracker(redis_client)

    try:
        # Step 1: Load document
        await tracker.update_status(job_id, "loading", "Loading document")

        loader_config = LoaderConfig(
            source_type=source_type,
            batch_size=config.get("batch_size", 10),
            extract_tables=config.get("extract_tables", True),
            ocr_enabled=config.get("ocr_enabled", True),
            languages=config.get("languages", ["vi", "en", "ar", "th", "id"]),
            metadata_filters=config.get("metadata_filters", {}),
        )

        # Select appropriate loader
        if source_type == "pdf":
            loader = PDFLoader()
        elif source_type == "html":
            loader = HTMLLoader()
        elif source_type == "docx":
            loader = DOCXLoader()
        else:
            raise ValueError(f"Unsupported source type: {source_type}")

        # Load documents (async generator)
        documents = []
        async for doc in loader.load(source, loader_config):
            documents.append(doc)

        if not documents:
            raise ValueError(f"No documents loaded from {source}")

        logger.info(f"Loaded {len(documents)} documents from {source}")

        # Step 2: Preprocess documents
        await tracker.update_status(job_id, "preprocessing", "Preprocessing documents")
        preprocessor = DocumentPreprocessor(
            enable_pii_redaction=config.get("redact_pii", True)
        )
        processed_docs = [preprocessor.process(doc) for doc in documents]

        # Step 3: Chunk documents
        await tracker.update_status(job_id, "chunking", "Chunking documents")
        chunker = MedicalChunker(
            max_tokens=config.get("max_chunk_tokens", 512),
            overlap=config.get("chunk_overlap", 50),
        )

        all_chunks = []
        for doc in processed_docs:
            chunks = chunker.chunk(
                doc, strategy=config.get("chunking_strategy", "medical")
            )
            all_chunks.extend(chunks)

        logger.info(
            f"Created {len(all_chunks)} chunks from {len(processed_docs)} documents"
        )

        # Step 4: Generate embeddings
        await tracker.update_status(job_id, "embedding", "Generating embeddings")
        embeddings_provider = EmbeddingsFactory.create(
            provider=config.get("embeddings_provider", "ollama"),
            use_cache=True,
            redis_client=redis_client,
        )

        chunk_texts = [chunk.content for chunk in all_chunks]
        embeddings = await embeddings_provider.embed_batch(
            chunk_texts,
            batch_size=config.get("embedding_batch_size", 32),
        )

        # Step 5: Store in vector database
        await tracker.update_status(job_id, "storing", "Storing in vector database")

        async with async_session_factory() as session:
            vector_store = PgVectorStore(
                session_factory=lambda: session,
                dimensions=embeddings_provider.dimensions,
            )

            # Initialize table if needed
            await vector_store.initialize()

            # Upsert chunks
            await vector_store.upsert(all_chunks, embeddings)

        # Mark as completed
        await tracker.update_status(
            job_id,
            "completed",
            processed=len(all_chunks),
        )

        await redis_client.close()

        return {
            "success": True,
            "documents_loaded": len(documents),
            "chunks_created": len(all_chunks),
            "source": source,
        }

    except Exception as e:
        logger.error(f"Ingestion failed for {source}: {e}", exc_info=True)

        await tracker.update_status(
            job_id,
            "failed",
            error=str(e),
        )

        await redis_client.close()

        return {
            "success": False,
            "error": str(e),
            "source": source,
        }


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="src.pharmaviyum.ai.rag.ingestion.tasks.ingest_document",
)
def ingest_document(
    self,
    source: str,
    source_type: str,
    job_id: str,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Celery task: Ingest a single document into the RAG pipeline.

    Args:
        source: Path or URL to the document
        source_type: "pdf", "html", or "docx"
        job_id: Unique job identifier for progress tracking
        config: Optional configuration overrides

    Returns:
        Dictionary with ingestion results
    """
    config = config or {}

    logger.info(f"Starting ingestion task: {job_id} ({source})")

    try:
        loop = get_event_loop()
        result = loop.run_until_complete(
            _ingest_document_async(source, source_type, job_id, config)
        )
        return result

    except Exception as exc:
        logger.error(f"Task failed with exception: {exc}", exc_info=True)

        # Retry on transient errors
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)

        return {
            "success": False,
            "error": str(exc),
            "source": source,
        }


@celery_app.task(
    bind=True,
    name="src.pharmaviyum.ai.rag.ingestion.tasks.ingest_batch",
)
def ingest_batch(
    self,
    sources: list[dict[str, str]],
    job_id: str,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Celery task: Ingest multiple documents in batch.

    Args:
        sources: List of {"source": str, "source_type": str}
        job_id: Unique job identifier
        config: Optional configuration

    Returns:
        Aggregated results
    """
    config = config or {}

    logger.info(f"Starting batch ingestion: {job_id} ({len(sources)} documents)")

    # Initialize progress tracker
    import redis

    redis_client = redis.from_url(settings.REDIS_URL)
    tracker = IngestionProgressTracker(redis_client)

    # Create job
    loop = get_event_loop()
    loop.run_until_complete(
        tracker.create_job(job_id, f"batch_{len(sources)}", len(sources), config)
    )

    results = []
    processed = 0
    failed = 0

    for i, source_info in enumerate(sources):
        source = source_info["source"]
        source_type = source_info["source_type"]

        logger.info(f"Processing document {i+1}/{len(sources)}: {source}")

        # Update progress
        loop.run_until_complete(
            tracker.update_status(
                job_id,
                "processing",
                f"Processing {i+1}/{len(sources)}",
                processed=processed,
                failed=failed,
            )
        )

        # Call single document task
        try:
            result = ingest_document.delay(
                source, source_type, f"{job_id}_doc_{i}", config
            )
            results.append(
                {
                    "source": source,
                    "task_id": result.id,
                    "status": "queued",
                }
            )
            processed += 1
        except Exception as e:
            logger.error(f"Failed to queue task for {source}: {e}")
            results.append(
                {
                    "source": source,
                    "status": "failed",
                    "error": str(e),
                }
            )
            failed += 1

    # Mark batch as completed (individual tasks will update their own status)
    loop.run_until_complete(
        tracker.update_status(
            job_id,
            "completed",
            processed=processed,
            failed=failed,
        )
    )

    redis_client.close()

    return {
        "success": True,
        "total_documents": len(sources),
        "queued": processed,
        "failed_to_queue": failed,
        "results": results,
    }


@celery_app.task(
    name="src.pharmaviyum.ai.rag.ingestion.tasks.cleanup_old_jobs",
)
def cleanup_old_jobs() -> dict[str, Any]:
    """Periodic task: Clean up old ingestion jobs from Redis."""
    import redis

    redis_client = redis.from_url(settings.REDIS_URL)
    tracker = IngestionProgressTracker(redis_client)

    loop = get_event_loop()
    removed = loop.run_until_complete(tracker.cleanup_old_jobs(days_old=7))

    redis_client.close()

    return {"removed_jobs": removed}
