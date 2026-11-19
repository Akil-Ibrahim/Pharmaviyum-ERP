"""Integration fault-injection tests for Redis connection recovery."""

import pytest
from redis.asyncio import Redis


@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_client_recovers_after_pool_connections_are_dropped(
    test_redis: Redis,
) -> None:
    """The Redis client reconnects after all currently pooled sockets are closed."""
    assert await test_redis.ping() is True

    # Simulate a broker/network restart from the client's perspective by
    # closing every pooled socket while leaving the isolated Redis service up.
    await test_redis.connection_pool.disconnect(inuse_connections=True)

    assert await test_redis.ping() is True
    await test_redis.set("fault-injection:recovery", "ok", ex=30)
    assert await test_redis.get("fault-injection:recovery") == "ok"
