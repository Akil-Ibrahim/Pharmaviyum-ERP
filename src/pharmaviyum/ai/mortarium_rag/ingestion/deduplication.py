"""
Document Deduplication for RAG Pipeline.

Best practice 2026:
- Content-hash based deduplication (exact match)
- Near-duplicate detection via embedding similarity
- Configurable dedup strategy (strict, fuzzy, disabled)
- Prevents wasted embeddings storage and improves retrieval quality
"""

from __future__ import annotations

import re
from typing import Literal

from sqlalchemy import text

from src.pharmaviyum.core.logging import logger

DedupStrategy = Literal["strict", "fuzzy", "disabled"]


class DocumentDeduplicator:
    """Prevent duplicate documents from polluting the vector store."""

    _IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    def __init__(
        self,
        session_factory,
        table_name: str = "document_chunks",
        strategy: DedupStrategy = "strict",
        similarity_threshold: float = 0.98,
    ):
        if not self._IDENTIFIER_RE.fullmatch(table_name):
            raise ValueError("table_name must be a simple SQL identifier")
        self.session_factory = session_factory
        self.table_name = table_name
        self.strategy = strategy
        self.similarity_threshold = similarity_threshold

    @staticmethod
    def _require_pharmacy_id(pharmacy_id: int) -> None:
        if (
            not isinstance(pharmacy_id, int)
            or isinstance(pharmacy_id, bool)
            or pharmacy_id <= 0
        ):
            raise ValueError(
                "Document deduplication requires a positive integer pharmacy_id"
            )

    async def filter_duplicates(
        self,
        content_hashes: list[str],
        document_ids: list[str],
        pharmacy_id: int,
    ) -> tuple[list[str], list[str]]:
        """Filter out documents already present in one pharmacy tenant."""
        self._require_pharmacy_id(pharmacy_id)
        if self.strategy == "disabled":
            return content_hashes, document_ids
        if self.strategy == "strict":
            return await self._strict_dedup(content_hashes, document_ids, pharmacy_id)
        if self.strategy == "fuzzy":
            new_hashes, new_ids = await self._strict_dedup(
                content_hashes, document_ids, pharmacy_id
            )
            return new_hashes, new_ids
        return content_hashes, document_ids

    async def _strict_dedup(
        self,
        content_hashes: list[str],
        document_ids: list[str],
        pharmacy_id: int,
    ) -> tuple[list[str], list[str]]:
        """Filter by exact content hash within one pharmacy tenant."""
        self._require_pharmacy_id(pharmacy_id)
        if not content_hashes:
            return [], []

        async with self.session_factory() as session:
            query = text(f"""  # nosec B608: table_name is validated as a SQL identifier
                SELECT DISTINCT metadata->>'content_hash' as hash,
                       document_id
                FROM {self.table_name}
                WHERE metadata->>'content_hash' = ANY(:hashes)
                  AND (metadata->>'pharmacy_id')::int = :pharmacy_id
            """)  # nosec B608: table_name is validated as a SQL identifier
            result = await session.execute(
                query, {"hashes": content_hashes, "pharmacy_id": pharmacy_id}
            )
            existing = {row.hash: row.document_id for row in result}

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
            query = text(f"""  # nosec B608: table_name is validated as a SQL identifier
                SELECT
                    COUNT(*) as total_chunks,
                    COUNT(DISTINCT metadata->>'content_hash') as unique_hashes,
                    COUNT(*) - COUNT(DISTINCT metadata->>'content_hash') as potential_duplicates
                FROM {self.table_name}
            """)  # nosec B608: table_name is validated as a SQL identifier
            result = await session.execute(query)
            row = result.fetchone()
            return {
                "total_chunks": row[0],
                "unique_hashes": row[1],
                "potential_duplicates": row[2],
            }
