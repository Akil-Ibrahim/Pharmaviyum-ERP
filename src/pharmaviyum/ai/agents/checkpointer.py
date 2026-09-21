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
        """Open the pool, initialize checkpoint tables, and return the saver."""
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
        await self._pool.open(wait=True)

        self._saver = AsyncPostgresSaver(conn=cast(Any, self._pool))
        await self._saver.setup()

        logger.info(
            "PostgreSQL LangGraph checkpointer initialized: %s",
            self.table_name,
            extra={
                "database": (
                    self.database_url.split("@")[-1]
                    if "@" in self.database_url
                    else "local"
                )
            },
        )
        return self._saver

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
