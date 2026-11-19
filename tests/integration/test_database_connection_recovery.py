"""Integration fault-injection tests for PostgreSQL pooled connection recovery."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pool_pre_ping_recovers_after_backend_is_terminated(
    test_engine: AsyncEngine,
) -> None:
    """A stale pooled connection is discarded and replaced after backend loss."""
    async with test_engine.connect() as connection:
        backend_pid = await connection.scalar(text("SELECT pg_backend_pid()"))

    assert isinstance(backend_pid, int)

    # Terminate the server-side session after it has returned to the pool.
    async with test_engine.connect() as control:
        terminated = await control.scalar(
            text("SELECT pg_terminate_backend(:pid)"),
            {"pid": backend_pid},
        )

    assert terminated is True

    # pool_pre_ping must detect the dead connection and transparently reconnect.
    async with test_engine.connect() as recovered:
        assert await recovered.scalar(text("SELECT 1")) == 1
