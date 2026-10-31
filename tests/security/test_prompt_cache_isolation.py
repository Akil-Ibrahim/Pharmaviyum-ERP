from __future__ import annotations

import pytest

from src.pharmaviyum.ai.harness.cache import PromptCache


class DummyRedis:
    async def get(self, key):
        return None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_prompt_cache_requires_user_and_pharmacy_scope() -> None:
    cache = PromptCache(DummyRedis())
    with pytest.raises(ValueError):
        await cache.get("question", {"pharmacy_id": 1})
    with pytest.raises(ValueError):
        await cache.get("question", {"user_id": "u1"})
    with pytest.raises(ValueError):
        await cache.set("question", {}, {"pharmacy_id": 1})
    with pytest.raises(ValueError):
        await cache.set("question", {}, {"user_id": "u1"})


def test_prompt_cache_key_changes_with_tenant_and_user() -> None:
    cache = PromptCache(DummyRedis())
    first = cache._build_cache_key("question", {"user_id": "u1", "pharmacy_id": 1})
    other_user = cache._build_cache_key("question", {"user_id": "u2", "pharmacy_id": 1})
    other_pharmacy = cache._build_cache_key(
        "question", {"user_id": "u1", "pharmacy_id": 2}
    )
    assert first != other_user
    assert first != other_pharmacy


class DummyEmbeddings:
    def __init__(self):
        self.calls = 0

    async def embed(self, text):
        self.calls += 1
        return [1.0, 0.0]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_semantic_cache_is_disabled_without_explicit_safe_opt_in() -> None:
    redis = DummyRedis()
    embeddings = DummyEmbeddings()
    cache = PromptCache(redis, embeddings_provider=embeddings)
    context = {"user_id": "u1", "pharmacy_id": 1}

    await cache.set("generic question", {"answer": "answer"}, context)
    assert embeddings.calls == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_semantic_cache_rejects_patient_specific_context() -> None:
    redis = DummyRedis()
    embeddings = DummyEmbeddings()
    cache = PromptCache(redis, embeddings_provider=embeddings)
    context = {
        "user_id": "u1",
        "pharmacy_id": 1,
        "patient_id": "patient-1",
        "semantic_cache_safe": True,
    }

    await cache.set("patient question", {"answer": "answer"}, context)
    assert embeddings.calls == 0


@pytest.mark.unit
def test_cache_key_changes_when_formulary_version_changes() -> None:
    cache = PromptCache(DummyRedis())
    first = cache._build_cache_key(
        "drug availability", {"user_id": "u1", "pharmacy_id": 1, "formulary_version": "v1"}
    )
    updated = cache._build_cache_key(
        "drug availability", {"user_id": "u1", "pharmacy_id": 1, "formulary_version": "v2"}
    )
    assert first != updated


@pytest.mark.unit
def test_semantic_cache_requires_trusted_opt_in_and_excludes_patient_scope() -> None:
    assert not PromptCache._semantic_cache_allowed(
        {"user_id": "u1", "pharmacy_id": 1}
    )
    assert PromptCache._semantic_cache_allowed(
        {
            "user_id": "u1",
            "pharmacy_id": 1,
            "semantic_cache_safe": True,
        }
    )
    assert not PromptCache._semantic_cache_allowed(
        {
            "user_id": "u1",
            "pharmacy_id": 1,
            "patient_id": 42,
            "semantic_cache_safe": True,
        }
    )
