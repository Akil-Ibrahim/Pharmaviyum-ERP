"""
Document Deduplication for RAG Pipeline.

Best practice 2026:
- Content-hash based deduplication (exact match)
- Near-duplicate detection via embedding similarity
- Configurable dedup strategy (strict, fuzzy, disabled)
- Prevents wasted embeddings storage and improves retrieval quality
"""

from __future__ import annotations

from typing import Literal

from sqlalchemy import text

from src.pharmaviyum.core.logging import logger

DedupStrategy = Literal["strict", "fuzzy", "disabled"]


class DocumentDeduplicator:
    """
    Prevents duplicate documents from polluting the vector store.

    Strategies:
    - strict: Exact content hash match (SHA-256)
    - fuzzy: Embedding similarity > 0.98 threshold
    - disabled: No deduplication
    """

    def __init__(
        self,
        session_factory,
        table_name: str = "document_chunks",
        strategy: DedupStrategy = "strict",
        similarity_threshold: float = 0.98,
    ):
        self.session_factory = session_factory
        self.table_name = table_name
        self.strategy = strategy
        self.similarity_threshold = similarity_threshold

    async def filter_duplicates(
        self,
        content_hashes: list[str],
        document_ids: list[str],
    ) -> tuple[list[str], list[str]]:
        """
        Filter out documents that already exist in the vector store.

        Returns:
            (new_hashes, new_document_ids) — only documents not yet in DB
        """
        if self.strategy == "disabled":
            return content_hashes, document_ids

        if self.strategy == "strict":
            return await self._strict_dedup(content_hashes, document_ids)

        if self.strategy == "fuzzy":
            # For fuzzy, we still do strict first, then check similarity
            new_hashes, new_ids = await self._strict_dedup(content_hashes, document_ids)
            # TODO: Implement fuzzy dedup via embedding similarity
            return new_hashes, new_ids

        return content_hashes, document_ids

    async def _strict_dedup(
        self,
        content_hashes: list[str],
        document_ids: list[str],
    ) -> tuple[list[str], list[str]]:
        """Filter by exact content hash match."""
        if not content_hashes:
            return [], []

        async with self.session_factory() as session:
            # Query for existing hashes in metadata
            query = text(
                f"""
                SELECT DISTINCT metadata->>'content_hash' as hash,
                       document_id
                FROM {self.table_name}
                WHERE metadata->>'content_hash' = ANY(:hashes)
            """
            )

            result = await session.execute(query, {"hashes": content_hashes})
            existing = {row.hash: row.document_id for row in result}

        # Filter out existing
        new_hashes = []
        new_ids = []
        duplicates_count = 0

        for h, doc_id in zip(content_hashes, document_ids):
            if h in existing:
                duplicates_count += 1
                logger.debug(f"Duplicate detected: doc {doc_id} (hash {h[:16]}...)")
            else:
                new_hashes.append(h)
                new_ids.append(doc_id)

        if duplicates_count > 0:
            logger.info(
                f"Deduplication: skipped {duplicates_count} duplicate documents"
            )

        return new_hashes, new_ids

    async def get_duplicate_stats(self) -> dict:
        """Get statistics about duplicates in the system."""
        async with self.session_factory() as session:
            query = text(
                f"""
                SELECT 
                    COUNT(*) as total_chunks,
                    COUNT(DISTINCT metadata->>'content_hash') as unique_hashes,
                    COUNT(*) - COUNT(DISTINCT metadata->>'content_hash') as potential_duplicates
                FROM {self.table_name}
            """
            )
            result = await session.execute(query)
            row = result.fetchone()

            return {
                "total_chunks": row[0],
                "unique_hashes": row[1],
                "potential_duplicates": row[2],
            }
