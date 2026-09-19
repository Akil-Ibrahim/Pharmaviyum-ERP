"""
Document Versioning for RAG Pipeline.

Best practice 2026:
- Track document versions via metadata
- Soft-delete old versions (mark as inactive, don't remove)
- Support for rollback to previous versions
- Version-aware retrieval (only active versions by default)
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from sqlalchemy import text

from src.pharmaviyum.core.logging import logger

VersionStatus = Literal["active", "archived", "deleted"]


class DocumentVersionManager:
    """Manage document versions in the vector store."""

    _IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    def __init__(
        self,
        session_factory,
        table_name: str = "document_chunks",
    ):
        if not self._IDENTIFIER_RE.fullmatch(table_name):
            raise ValueError("table_name must be a simple SQL identifier")
        self.session_factory = session_factory
        self.table_name = table_name

    @staticmethod
    def _require_pharmacy_id(pharmacy_id: int) -> None:
        if not isinstance(pharmacy_id, int) or isinstance(pharmacy_id, bool) or pharmacy_id <= 0:
            raise ValueError("Document versioning requires a positive integer pharmacy_id")

    async def archive_old_versions(self, source: str, new_version: int, pharmacy_id: int) -> int:
        """Archive previous versions within one pharmacy tenant."""
        self._require_pharmacy_id(pharmacy_id)
        async with self.session_factory() as session:
            query = text(  # nosec B608: table_name is validated as a SQL identifier
                f"""  # nosec B608: table_name is validated as a SQL identifier
                UPDATE {self.table_name}
                SET metadata = jsonb_set(
                    metadata,
                    '{{version_status}}',
                    '"archived"'
                ) || jsonb_build_object(
                    'superseded_by_version', :new_version::text,
                    'archived_at', :now::text
                )
                WHERE metadata->>'source' = :source
                  AND (metadata->>'pharmacy_id')::int = :pharmacy_id
                  AND (metadata->>'version_status' IS NULL
                       OR metadata->>'version_status' = 'active')
                  AND (metadata->>'version_number')::int < :new_version
            """
            )
            result = await session.execute(
                query,
                {
                    "source": source,
                    "pharmacy_id": pharmacy_id,
                    "new_version": new_version,
                    "now": datetime.utcnow().isoformat(),
                },
            )
            await session.commit()
            archived_count = result.rowcount
            if archived_count > 0:
                logger.info(
                    f"Archived {archived_count} chunks from previous versions of {source}"
                )
            return archived_count

    async def get_next_version(self, source: str, pharmacy_id: int) -> int:
        """Get the next version within one pharmacy tenant."""
        self._require_pharmacy_id(pharmacy_id)
        async with self.session_factory() as session:
            query = text(  # nosec B608: table_name is validated as a SQL identifier
                f"""  # nosec B608: table_name is validated as a SQL identifier
                SELECT COALESCE(
                    MAX((metadata->>'version_number')::int),
                    0
                ) + 1
                FROM {self.table_name}
                WHERE metadata->>'source' = :source
                  AND (metadata->>'pharmacy_id')::int = :pharmacy_id
            """
            )
            result = await session.execute(query, {"source": source, "pharmacy_id": pharmacy_id})
            return result.scalar_one()

    async def rollback_to_version(self, source: str, target_version: int, pharmacy_id: int) -> int:
        """Rollback to a previous version within one pharmacy tenant."""
        self._require_pharmacy_id(pharmacy_id)
        async with self.session_factory() as session:
            archive_query = text(  # nosec B608: table_name is validated as a SQL identifier
                f"""  # nosec B608: table_name is validated as a SQL identifier
                UPDATE {self.table_name}
                SET metadata = jsonb_set(
                    metadata,
                    '{{version_status}}',
                    '"archived"'
                )
                WHERE metadata->>'source' = :source
                  AND (metadata->>'pharmacy_id')::int = :pharmacy_id
                  AND metadata->>'version_status' = 'active'
            """
            )
            await session.execute(archive_query, {"source": source, "pharmacy_id": pharmacy_id})

            restore_query = text(  # nosec B608: table_name is validated as a SQL identifier
                f"""  # nosec B608: table_name is validated as a SQL identifier
                UPDATE {self.table_name}
                SET metadata = jsonb_set(
                    metadata,
                    '{{version_status}}',
                    '"active"'
                ) - 'superseded_by_version' - 'archived_at'
                WHERE metadata->>'source' = :source
                  AND (metadata->>'version_number')::int = :target_version
            """
            )
            result = await session.execute(
                restore_query,
                {"source": source, "pharmacy_id": pharmacy_id, "target_version": target_version},
            )
            await session.commit()
            restored_count = result.rowcount
            logger.info(
                f"Rolled back {source} to version {target_version} ({restored_count} chunks)"
            )
            return restored_count

    async def get_version_history(self, source: str, pharmacy_id: int) -> list[dict]:
        """Get version history within one pharmacy tenant."""
        self._require_pharmacy_id(pharmacy_id)
        async with self.session_factory() as session:
            query = text(  # nosec B608: table_name is validated as a SQL identifier
                f"""  # nosec B608: table_name is validated as a SQL identifier
                SELECT
                    (metadata->>'version_number')::int as version,
                    metadata->>'version_status' as status,
                    COUNT(*) as chunk_count,
                    MIN(created_at) as first_seen,
                    MAX(created_at) as last_updated
                FROM {self.table_name}
                WHERE metadata->>'source' = :source
                  AND (metadata->>'pharmacy_id')::int = :pharmacy_id
                  AND metadata->>'version_number' IS NOT NULL
                GROUP BY version, status
                ORDER BY version DESC
            """
            )
            result = await session.execute(query, {"source": source, "pharmacy_id": pharmacy_id})
            return [
                {
                    "version": row.version,
                    "status": row.status,
                    "chunk_count": row.chunk_count,
                    "first_seen": (
                        row.first_seen.isoformat() if row.first_seen else None
                    ),
                    "last_updated": (
                        row.last_updated.isoformat() if row.last_updated else None
                    ),
                }
                for row in result
            ]
