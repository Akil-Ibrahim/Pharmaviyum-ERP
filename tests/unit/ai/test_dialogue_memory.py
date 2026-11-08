from __future__ import annotations

import json

import pytest

from src.pharmaviyum.ai.harness.memory import DialogueMemory


class FakePipeline:
    def __init__(self, redis):
        self.redis = redis
        self.operations = []

    def __getattr__(self, name):
        def queue(*args):
            self.operations.append((name, args))
            return self
        return queue

    async def execute(self):
        results = []
        for name, args in self.operations:
            method = getattr(self.redis, name)
            result = method(*args)
            if hasattr(result, "__await__"):
                result = await result
            results.append(result)
        return results


class FakeRedis:
    def __init__(self):
        self.lists = {}
        self.values = {}
        self.hashes = {}

    def pipeline(self):
        return FakePipeline(self)

    async def rpush(self, key, *values):
        self.lists.setdefault(key, []).extend(values)
        return len(self.lists[key])

    async def lrange(self, key, start, stop):
        values = self.lists.get(key, [])
        return values[start : stop + 1 if stop != -1 else None]

    async def ltrim(self, key, start, stop):
        self.lists[key] = await self.lrange(key, start, stop)
        return True

    async def llen(self, key):
        return len(self.lists.get(key, []))

    async def get(self, key):
        return self.values.get(key)

    async def setex(self, key, ttl, value):
        self.values[key] = value
        return True

    async def expire(self, key, ttl):
        return True

    async def delete(self, key):
        self.lists.pop(key, None)
        self.values.pop(key, None)
        self.hashes.pop(key, None)
        return 1

    async def hset(self, key, field, value):
        self.hashes.setdefault(key, {})[field] = value

    async def hgetall(self, key):
        return self.hashes.get(key, {})


class FakeSummarizer:
    async def ainvoke(self, prompt):
        assert "untrusted quoted data" in prompt
        return type("Result", (), {"content": "A factual rolling summary."})()


class FailingSummarizer:
    async def ainvoke(self, prompt):
        raise RuntimeError("provider unavailable")


@pytest.mark.asyncio
async def test_raw_turns_are_retained_when_summarizer_is_not_configured():
    redis = FakeRedis()
    memory = DialogueMemory(redis, summarization_threshold=2)

    await memory.save("session-1", "first question", "first answer")
    await memory.save("session-1", "second question", "second answer")

    key = f"{memory._session_prefix('session-1')}:messages"
    assert await redis.llen(key) == 4
    assert not redis.lists.get(f"{memory._session_prefix('session-1')}:archive")


@pytest.mark.asyncio
async def test_successful_compaction_archives_verbatim_turns_before_trimming():
    redis = FakeRedis()
    memory = DialogueMemory(
        redis, summarizer=FakeSummarizer(), summarization_threshold=2
    )

    await memory.save("session-1", "first question", "first answer")
    await memory.save("session-1", "second question", "second answer")

    session_prefix = memory._session_prefix("session-1")
    active_key = f"{session_prefix}:messages"
    archive_key = f"{session_prefix}:archive"
    summary_key = f"{session_prefix}:summary"
    assert await redis.llen(active_key) == 2
    assert len(redis.lists[archive_key]) == 2
    archived = [json.loads(item) for item in redis.lists[archive_key]]
    assert archived[0]["content"] == "first question"
    assert archived[1]["content"] == "first answer"
    assert redis.values[summary_key] == "A factual rolling summary."


@pytest.mark.asyncio
async def test_failed_summarization_does_not_trim_or_archive_source_turns():
    redis = FakeRedis()
    memory = DialogueMemory(
        redis, summarizer=FailingSummarizer(), summarization_threshold=2
    )

    await memory.save("session-1", "first question", "first answer")
    await memory.save("session-1", "second question", "second answer")

    session_prefix = memory._session_prefix("session-1")
    assert await redis.llen(f"{session_prefix}:messages") == 4
    assert not redis.lists.get(f"{session_prefix}:archive")
    assert await redis.get(f"{session_prefix}:summary") is None


def test_memory_redis_namespace_is_opaque_and_keyed(monkeypatch):
    from src.pharmaviyum.core.config import settings as app_settings

    monkeypatch.setattr(app_settings, "SECRET_KEY", "first-memory-secret")
    first = DialogueMemory._session_prefix(
        "pharmacy:7:user:42:session:conversation-123"
    )
    monkeypatch.setattr(app_settings, "SECRET_KEY", "rotated-memory-secret")
    second = DialogueMemory._session_prefix(
        "pharmacy:7:user:42:session:conversation-123"
    )

    assert first.startswith("agent:memory:v2:")
    assert first != second
    assert "pharmacy" not in first
    assert "user" not in first
    assert "conversation-123" not in first


def test_memory_redis_namespace_fails_closed_without_production_secret(monkeypatch):
    from src.pharmaviyum.core.config import Environment, settings as app_settings

    monkeypatch.setattr(app_settings, "SECRET_KEY", None)
    monkeypatch.setattr(app_settings, "ENVIRONMENT", Environment.PRODUCTION)

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        DialogueMemory._session_prefix("session-1")


@pytest.mark.parametrize("session_id", ["", "   ", "x" * 513, 123])
def test_memory_redis_namespace_rejects_invalid_session_id(session_id):
    with pytest.raises(ValueError, match="session identifier"):
        DialogueMemory._session_prefix(session_id)


@pytest.mark.asyncio
async def test_clear_removes_current_and_exact_legacy_memory_keys():
    redis = FakeRedis()
    memory = DialogueMemory(redis)
    session_id = "session-1"
    current_prefix = memory._session_prefix(session_id)
    legacy_prefix = f"agent:memory:{session_id}"

    await redis.rpush(f"{current_prefix}:messages", "current")
    await redis.rpush(f"{legacy_prefix}:messages", "legacy")

    await memory.clear(session_id)

    assert await redis.llen(f"{current_prefix}:messages") == 0
    assert await redis.llen(f"{legacy_prefix}:messages") == 0
