"""
LangGraph state persistence with a PostgreSQL-backed async checkpointer.

The saver owns an AsyncConnectionPool for the lifetime of the application.
This avoids handing a closed context-managed AsyncPostgresSaver to a compiled
LangGraph graph.
"""

from __future__ import annotations

from typing import Any, cast

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

from src.pharmaviyum.core.logging import logger


class AgentCheckpointer:
    """Production PostgreSQL checkpointer with application-lifetime pooling."""

    def __init__(
        self,
        database_url: str,
        table_name: str = "agent_checkpoints",
        max_size: int = 20,
    ) -> None:
        self.database_url = database_url
        self.table_name = table_name
        self.max_size = max_size
        self._pool: AsyncConnectionPool | None = None
        self._saver: AsyncPostgresSaver | None = None

    async def initialize(self) -> AsyncPostgresSaver:
        """Open the pool and verify Alembic-managed checkpoint tables."""
        if self._saver is not None:
            return self._saver

        self._pool = AsyncConnectionPool(
            conninfo=self.database_url,
            min_size=1,
            max_size=self.max_size,
            open=False,
            kwargs={
                "autocommit": True,
                "prepare_threshold": 0,
            },
        )
        try:
            await self._pool.open(wait=True)
            self._saver = AsyncPostgresSaver(conn=cast(Any, self._pool))
            await self._verify_schema()
        except Exception:
            await self.close()
            raise

        logger.info(
            "PostgreSQL LangGraph checkpointer initialized",
            extra={"table": self.table_name},
        )
        return self._saver

    async def _verify_schema(self) -> None:
        """Fail closed unless the pinned LangGraph checkpoint schema is migrated."""
        if self._pool is None or self._saver is None:
            raise RuntimeError("LangGraph checkpoint pool is not initialized")

        async with self._pool.connection() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute("""
                    SELECT
                        to_regclass('public.checkpoint_migrations') IS NOT NULL,
                        to_regclass('public.checkpoints') IS NOT NULL,
                        to_regclass('public.checkpoint_blobs') IS NOT NULL,
                        to_regclass('public.checkpoint_writes') IS NOT NULL,
                        EXISTS (
                            SELECT 1
                            FROM pg_attribute
                            WHERE attrelid = to_regclass('public.checkpoint_writes')
                              AND attname = 'task_path'
                              AND NOT attisdropped
                        ),
                        EXISTS (
                            SELECT 1
                            FROM pg_attribute
                            WHERE attrelid = to_regclass('public.checkpoint_blobs')
                              AND attname = 'blob'
                              AND NOT attisdropped
                              AND NOT attnotnull
                        ),
                        COALESCE(
                            (
                                SELECT array_agg(indexname)
                                FROM pg_indexes
                                WHERE schemaname = 'public'
                                  AND indexname IN (
                                      'checkpoints_thread_id_idx',
                                      'checkpoint_blobs_thread_id_idx',
                                      'checkpoint_writes_thread_id_idx'
                                  )
                            ),
                            ARRAY[]::text[]
                        )
                    """)
                schema = await cursor.fetchone()

                if schema is None or not all(schema[:6]):
                    raise RuntimeError(
                        "LangGraph checkpoint schema is incomplete; "
                        "apply the Alembic database migrations."
                    )

                await cursor.execute("SELECT max(v) FROM public.checkpoint_migrations")
                version_row = await cursor.fetchone()

        expected_version = len(self._saver.MIGRATIONS) - 1
        actual_version = version_row[0] if version_row is not None else None
        if actual_version != expected_version:
            raise RuntimeError(
                "LangGraph checkpoint schema version mismatch: "
                f"expected={expected_version}, actual={actual_version}. "
                "Apply the Alembic database migrations using the pinned "
                "langgraph-checkpoint-postgres version."
            )

        required_indexes = {
            "checkpoints_thread_id_idx",
            "checkpoint_blobs_thread_id_idx",
            "checkpoint_writes_thread_id_idx",
        }
        existing_indexes = set(schema[6] or ())
        missing_indexes = sorted(required_indexes - existing_indexes)
        if missing_indexes:
            raise RuntimeError(
                "LangGraph checkpoint schema is missing indexes: "
                + ", ".join(missing_indexes)
                + ". Apply the Alembic database migrations."
            )

    async def close(self) -> None:
        """Close the application-lifetime PostgreSQL pool."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            self._saver = None
            logger.info("LangGraph checkpointer pool closed")

    @property
    def saver(self) -> AsyncPostgresSaver | None:
        """Get the initialized PostgreSQL saver."""
        return self._saver

    @property
    def pool(self) -> Any | None:
        """Get the underlying connection pool for application lifecycle hooks."""
        return self._pool
