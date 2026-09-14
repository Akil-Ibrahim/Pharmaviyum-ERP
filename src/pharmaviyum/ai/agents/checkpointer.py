"""
LangGraph State Persistence with Checkpointer.

Best practice 2026:
- PostgresSaver for production (durable, queryable)
- Automatic state snapshot after each node execution
- Enables time-travel debugging in LangSmith
- Supports conversation resumption after failures
"""
from __future__ import annotations
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy.ext.asyncio import create_async_engine
from src.pharmaviyum.core.logging import logger


class AgentCheckpointer:
    """
    Production-ready checkpointer using PostgreSQL.
    
    Features:
    - Automatic state persistence after each node
    - Thread-based conversation isolation
    - Time-travel debugging support
    - Retry after failures (resume from last checkpoint)
    """
    
    def __init__(
        self,
        database_url: str,
        table_name: str = "agent_checkpoints",
    ):
        self.database_url = database_url
        self.table_name = table_name
        self._saver = None
        self._engine = None
    
    async def initialize(self) -> AsyncPostgresSaver:
        """Initialize the checkpointer and create tables."""
        if self._saver is None:
            self._engine = create_async_engine(
                self.database_url,
                echo=False,
                pool_pre_ping=True,
            )
            
            self._saver = AsyncPostgresSaver.from_conn_string(self.database_url)
            
            # Create checkpoint tables
            await self._saver.setup()
            
            logger.info(
                f"Agent checkpointer initialized: {self.table_name}",
                extra={"database": self.database_url.split("@")[-1] if "@" in self.database_url else "local"}
            )
        
        return self._saver
    
    async def close(self):
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()
            logger.info("Agent checkpointer closed")
    
    @property
    def saver(self) -> AsyncPostgresSaver | None:
        """Get the underlying PostgresSaver instance."""
        return self._saver
