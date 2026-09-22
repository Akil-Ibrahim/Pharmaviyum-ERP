"""
Ingestion Orchestrator — Main coordinator for the RAG pipeline.

Best practice 2026:
- Single entry point for all ingestion operations
- Coordinates: loader → preprocessor → deduplicator → versioner → chunker → embeddings → vector store
- Async-first design
- Structured result reporting
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any, Literal, cast

from src.pharmaviyum.core.logging import logger

from ..chunking import MedicalChunker
from ..embeddings import EmbeddingsFactory
from .loaders import DOCXLoader, HTMLLoader, LoadedDocument, LoaderConfig, PDFLoader
from ..preprocessing import DocumentPreprocessor
from ..vector_store import PgVectorStore
from .deduplication import DedupStrategy, DocumentDeduplicator
from .versioning import DocumentVersionManager


class IngestionOrchestrator:
    """
    Main orchestrator for the RAG ingestion pipeline.

    Usage:
        orchestrator = IngestionOrchestrator(session_factory, redis_client)
        result = await orchestrator.ingest_file(
            source="/path/to/guideline.pdf",
            source_type="pdf",
            config={"country": "VN", "language": "vi"}
        )
    """

    def __init__(
        self,
        session_factory,
        redis_client,
        embeddings_provider: str = "ollama",
        embeddings_api_key: str | None = None,
        embeddings_model: str | None = None,
        embeddings_dimensions: int = 1024,
        dedup_strategy: DedupStrategy = "strict",
        enable_versioning: bool = True,
        enable_pii_redaction: bool = True,
    ):
        self.session_factory = session_factory
        self.redis_client = redis_client
        self.embeddings_provider = embeddings_provider
        self.embeddings_api_key = embeddings_api_key
        self.embeddings_model = embeddings_model
        self.embeddings_dimensions = embeddings_dimensions
        self.dedup_strategy = dedup_strategy
        self.enable_versioning = enable_versioning

        self.preprocessor = DocumentPreprocessor(
            enable_pii_redaction=enable_pii_redaction
        )
        self.deduplicator = DocumentDeduplicator(
            session_factory=session_factory,
            strategy=dedup_strategy,
        )
        self.version_manager = DocumentVersionManager(session_factory=session_factory)

    async def ingest_file(
        self,
        source: str,
        source_type: str | None = None,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Ingest a single file through the full RAG pipeline."""
        start_time = time.perf_counter()
        config = config or {}
        job_id = str(uuid.uuid4())

        logger.info("Starting ingestion task", extra={"job_id": job_id})

        stats: dict[str, Any] = {
            "job_id": job_id,
            "source": source,
            "documents_loaded": 0,
            "documents_preprocessed": 0,
            "duplicates_skipped": 0,
            "chunks_created": 0,
            "chunks_stored": 0,
            "errors": [],
        }

        try:
            loader = self._get_loader(source, source_type)
            loader_source_type = cast(
                Literal["pdf", "html", "docx", "database", "web", "file"],
                source_type or self._detect_source_type(source),
            )
            loader_config = LoaderConfig(
                source_type=loader_source_type,
                batch_size=config.get("batch_size", 10),
                extract_tables=config.get("extract_tables", True),
                ocr_enabled=config.get("ocr_enabled", True),
                languages=config.get("languages", ["vi", "en", "ar", "th", "id"]),
                metadata_filters=config,
            )

            documents: list[LoadedDocument] = []
            async for doc in loader.load(source, loader_config):
                documents.append(doc)

            stats["documents_loaded"] = len(documents)
            logger.info(
                "Loaded documents", extra={"job_id": job_id, "count": len(documents)}
            )

            if not documents:
                raise ValueError(f"No documents loaded from {source}")

            processed_docs: list[LoadedDocument] = []
            for doc in documents:
                try:
                    processed = self.preprocessor.process(doc)
                    processed_docs.append(processed)
                except Exception as e:
                    logger.warning(f"Preprocessing failed for doc: {e}")
                    stats["errors"].append(f"preprocess_error: {e}")

            stats["documents_preprocessed"] = len(processed_docs)

            content_hashes = [
                doc.metadata.get("content_hash", "") for doc in processed_docs
            ]
            doc_ids = [str(doc.id) for doc in processed_docs]

            pharmacy_id = config.get("pharmacy_id")
            if (
                not isinstance(pharmacy_id, int)
                or isinstance(pharmacy_id, bool)
                or pharmacy_id <= 0
            ):
                raise ValueError(
                    "RAG ingestion requires a positive integer pharmacy_id"
                )

            new_hashes, new_doc_ids = await self.deduplicator.filter_duplicates(
                content_hashes, doc_ids, pharmacy_id
            )

            stats["duplicates_skipped"] = len(processed_docs) - len(new_doc_ids)

            if stats["duplicates_skipped"] > 0:
                new_doc_id_set = set(new_doc_ids)
                processed_docs = [
                    doc for doc in processed_docs if str(doc.id) in new_doc_id_set
                ]

            if not processed_docs:
                logger.info("All documents were duplicates", extra={"job_id": job_id})
                stats["latency_ms"] = (time.perf_counter() - start_time) * 1000
                return {
                    **stats,
                    "success": True,
                    "message": "All documents were duplicates",
                }

            if self.enable_versioning:
                new_version = await self.version_manager.get_next_version(
                    source, pharmacy_id
                )
                await self.version_manager.archive_old_versions(
                    source, new_version, pharmacy_id
                )
                for doc in processed_docs:
                    doc.metadata["version_number"] = new_version
                    doc.metadata["version_status"] = "active"

            chunker = MedicalChunker(
                max_tokens=config.get("max_chunk_tokens", 512),
                overlap=config.get("chunk_overlap", 50),
            )

            all_chunks: list[Any] = []
            for doc in processed_docs:
                chunks = chunker.chunk(
                    doc, strategy=config.get("chunking_strategy", "medical")
                )
                all_chunks.extend(chunks)

            stats["chunks_created"] = len(all_chunks)
            logger.info(f"Created {len(all_chunks)} chunks")

            embeddings_provider = EmbeddingsFactory.create(
                provider=self.embeddings_provider,
                use_cache=True,
                redis_client=self.redis_client,
                api_key=self.embeddings_api_key,
                model=self.embeddings_model,
                dimensions=self.embeddings_dimensions,
            )

            chunk_texts = [chunk.content for chunk in all_chunks]
            embeddings = await embeddings_provider.embed_batch(
                chunk_texts,
                batch_size=config.get("embedding_batch_size", 32),
            )

            async with self.session_factory() as session:
                vector_store = PgVectorStore(
                    session_factory=lambda: session,
                    dimensions=embeddings_provider.dimensions,
                )
                await vector_store.initialize()
                stored_count = await vector_store.upsert(all_chunks, embeddings)

            stats["chunks_stored"] = stored_count
            latency_ms = (time.perf_counter() - start_time) * 1000
            stats["latency_ms"] = latency_ms

            logger.info(
                f"Ingestion completed: {source}",
                extra={
                    "job_id": job_id,
                    "chunks_stored": stored_count,
                    "latency_ms": latency_ms,
                },
            )

            return {**stats, "success": True}

        except Exception as e:
            logger.error("Ingestion failed", extra={"job_id": job_id}, exc_info=True)
            stats["errors"].append(f"fatal: {str(e)}")
            stats["latency_ms"] = (time.perf_counter() - start_time) * 1000
            return {**stats, "success": False, "error": str(e)}

    async def ingest_batch(
        self,
        sources: list[dict[str, str]],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Ingest multiple files in batch."""
        results: list[dict[str, Any]] = []
        total_chunks = 0
        total_errors = 0

        for source_info in sources:
            result = await self.ingest_file(
                source=source_info["source"],
                source_type=source_info.get("source_type"),
                config=config,
            )
            results.append(result)

            if result["success"]:
                total_chunks += result.get("chunks_stored", 0)
            else:
                total_errors += 1

        return {
            "success": total_errors == 0,
            "total_sources": len(sources),
            "successful": len(sources) - total_errors,
            "failed": total_errors,
            "total_chunks_stored": total_chunks,
            "results": results,
        }

    def _get_loader(self, source: str, source_type: str | None):
        """Get appropriate loader for source."""
        detected_type = source_type or self._detect_source_type(source)

        if detected_type == "pdf":
            return PDFLoader()
        if detected_type == "html":
            return HTMLLoader()
        if detected_type == "docx":
            return DOCXLoader()
        raise ValueError(f"Unsupported source type: {detected_type}")

    def _detect_source_type(self, source: str) -> str:
        """Detect source type from file extension or URL."""
        if source.startswith(("http://", "https://")):
            return "html"

        ext = Path(source).suffix.lower()
        type_map = {
            ".pdf": "pdf",
            ".html": "html",
            ".htm": "html",
            ".docx": "docx",
        }

        return type_map.get(ext, "pdf")
