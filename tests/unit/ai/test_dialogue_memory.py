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

    key = "agent:memory:session-1:messages"
    assert await redis.llen(key) == 4
    assert not redis.lists.get("agent:memory:session-1:archive")


@pytest.mark.asyncio
async def test_successful_compaction_archives_verbatim_turns_before_trimming():
    redis = FakeRedis()
    memory = DialogueMemory(
        redis, summarizer=FakeSummarizer(), summarization_threshold=2
    )

    await memory.save("session-1", "first question", "first answer")
    await memory.save("session-1", "second question", "second answer")

    active_key = "agent:memory:session-1:messages"
    archive_key = "agent:memory:session-1:archive"
    summary_key = "agent:memory:session-1:summary"
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

    assert await redis.llen("agent:memory:session-1:messages") == 4
    assert not redis.lists.get("agent:memory:session-1:archive")
    assert await redis.get("agent:memory:session-1:summary") is None
