"""Unit tests for Redis connection initialization and recovery."""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
from redis.exceptions import ConnectionError

import src.pharmaviyum.redis_client as redis_client


@pytest.fixture(autouse=True)
def reset_redis_globals(monkeypatch):
    monkeypatch.setattr(redis_client, "_redis_client", None)
    monkeypatch.setattr(redis_client, "_pool", None)


@pytest.mark.asyncio
async def test_failed_initial_ping_does_not_cache_client(monkeypatch):
    first = Mock()
    first.ping = AsyncMock(side_effect=ConnectionError("Redis unavailable"))
    second = Mock()
    second.ping = AsyncMock(return_value=True)
    clients = [first, second]
    factory = Mock(side_effect=clients)

    monkeypatch.setattr(redis_client, "Redis", factory)
    monkeypatch.setattr(redis_client, "get_redis_pool", Mock(return_value=object()))

    async def execute(_operation, command):
        return await command()

    monkeypatch.setattr(redis_client, "_execute_redis_command", execute)

    with pytest.raises(ConnectionError):
        await redis_client.get_redis()

    assert redis_client._redis_client is None
    recovered = await redis_client.get_redis()

    assert recovered is second
    assert factory.call_count == 2


@pytest.mark.asyncio
async def test_concurrent_initialization_creates_one_client(monkeypatch):
    client = Mock()
    client.ping = AsyncMock(return_value=True)
    factory = Mock(return_value=client)
    monkeypatch.setattr(redis_client, "Redis", factory)
    monkeypatch.setattr(redis_client, "get_redis_pool", Mock(return_value=object()))

    async def execute(_operation, command):
        await asyncio.sleep(0)
        return await command()

    monkeypatch.setattr(redis_client, "_execute_redis_command", execute)

    first, second = await asyncio.gather(
        redis_client.get_redis(),
        redis_client.get_redis(),
    )

    assert first is client
    assert second is client
    assert factory.call_count == 1
    client.ping.assert_awaited_once()


def test_redis_pool_uses_bounded_connection_timeouts(monkeypatch):
    from src.pharmaviyum.config import settings

    from_url = Mock(return_value=object())
    monkeypatch.setattr(redis_client.ConnectionPool, "from_url", from_url)

    redis_client.get_redis_pool()

    kwargs = from_url.call_args.kwargs
    assert kwargs["socket_connect_timeout"] == settings.REDIS_CONNECT_TIMEOUT_SECONDS
    assert kwargs["socket_timeout"] == settings.REDIS_SOCKET_TIMEOUT_SECONDS
    assert kwargs["retry_on_timeout"] is True
