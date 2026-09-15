"""
Document Versioning for RAG Pipeline.

Best practice 2026:
- Track document versions via metadata
- Soft-delete old versions (mark as inactive, don't remove)
- Support for rollback to previous versions
- Version-aware retrieval (only active versions by default)
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from sqlalchemy import text

from src.pharmaviyum.core.logging import logger

VersionStatus = Literal["active", "archived", "deleted"]


class DocumentVersionManager:
    """
    Manages document versions in the vector store.

    Features:
    - Version tracking via metadata (version_number, is_active, superseded_by)
    - Soft-delete for audit trail
    - Version-aware filtering in vector search
    """

    def __init__(
        self,
        session_factory,
        table_name: str = "document_chunks",
    ):
        self.session_factory = session_factory
        self.table_name = table_name

    async def archive_old_versions(
        self,
        source: str,
        new_version: int,
    ) -> int:
        """
        Archive all previous versions of a document source.

        Marks old chunks as 'archived' and links them to the new version.

        Returns:
            Number of chunks archived
        """
        async with self.session_factory() as session:
            # Find all active chunks for this source with older versions
            query = text(
                f"""
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
                  AND (metadata->>'version_status' IS NULL 
                       OR metadata->>'version_status' = 'active')
                  AND (metadata->>'version_number')::int < :new_version
            """
            )

            result = await session.execute(
                query,
                {
                    "source": source,
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

    async def get_next_version(self, source: str) -> int:
        """Get the next version number for a document source."""
        async with self.session_factory() as session:
            query = text(
                f"""
                SELECT COALESCE(
                    MAX((metadata->>'version_number')::int),
                    0
                ) + 1
                FROM {self.table_name}
                WHERE metadata->>'source' = :source
            """
            )

            result = await session.execute(query, {"source": source})
            return result.scalar_one()

    async def rollback_to_version(
        self,
        source: str,
        target_version: int,
    ) -> int:
        """
        Rollback: archive current version and restore target version.

        Returns:
            Number of chunks affected
        """
        async with self.session_factory() as session:
            # Archive current active version
            archive_query = text(
                f"""
                UPDATE {self.table_name}
                SET metadata = jsonb_set(
                    metadata,
                    '{{version_status}}',
                    '"archived"'
                )
                WHERE metadata->>'source' = :source
                  AND metadata->>'version_status' = 'active'
            """
            )
            await session.execute(archive_query, {"source": source})

            # Restore target version
            restore_query = text(
                f"""
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
                {
                    "source": source,
                    "target_version": target_version,
                },
            )

            await session.commit()
            restored_count = result.rowcount

            logger.info(
                f"Rolled back {source} to version {target_version} ({restored_count} chunks)"
            )
            return restored_count

    async def get_version_history(self, source: str) -> list[dict]:
        """Get version history for a document source."""
        async with self.session_factory() as session:
            query = text(
                f"""
                SELECT 
                    (metadata->>'version_number')::int as version,
                    metadata->>'version_status' as status,
                    COUNT(*) as chunk_count,
                    MIN(created_at) as first_seen,
                    MAX(created_at) as last_updated
                FROM {self.table_name}
                WHERE metadata->>'source' = :source
                  AND metadata->>'version_number' IS NOT NULL
                GROUP BY version, status
                ORDER BY version DESC
            """
            )

            result = await session.execute(query, {"source": source})
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
