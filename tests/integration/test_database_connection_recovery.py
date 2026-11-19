"""Integration fault-injection tests for PostgreSQL pooled connection recovery."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pool_pre_ping_recovers_after_backend_is_terminated(
    test_engine: AsyncEngine,
) -> None:
    """A stale idle pooled connection is discarded and replaced after backend loss."""
    # Return the victim connection to the pool before terminating its backend.
    # Terminating a checked-out asyncpg connection can race with SQLAlchemy's
    # rollback-on-return and produce an asyncpg protocol-state error.
    async with test_engine.connect() as victim:
        backend_pid = await victim.scalar(text("SELECT pg_backend_pid()"))
        assert isinstance(backend_pid, int)

    # Use a separate, non-pooling control connection so the termination command
    # cannot accidentally run on (and terminate) the victim connection itself.
    from src.pharmaviyum.config import settings

    control_engine = create_async_engine(
        settings.DATABASE_URL,
        poolclass=NullPool,
    )
    try:
        async with control_engine.connect() as control:
            terminated = await control.scalar(
                text("SELECT pg_terminate_backend(:pid)"),
                {"pid": backend_pid},
            )
    finally:
        await control_engine.dispose()

    assert terminated is True

    # The next checkout must run pool_pre_ping, discard the dead DBAPI
    # connection, and establish a fresh PostgreSQL backend transparently.
    async with test_engine.connect() as recovered:
        assert await recovered.scalar(text("SELECT 1")) == 1
        recovered_pid = await recovered.scalar(text("SELECT pg_backend_pid()"))
        assert recovered_pid != backend_pid
