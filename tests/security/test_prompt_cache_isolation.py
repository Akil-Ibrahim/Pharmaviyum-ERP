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


def test_prompt_cache_key_changes_with_tenant_and_user() -> None:
    cache = PromptCache(DummyRedis())
    first = cache._build_cache_key("question", {"user_id": "u1", "pharmacy_id": 1})
    other_user = cache._build_cache_key("question", {"user_id": "u2", "pharmacy_id": 1})
    other_pharmacy = cache._build_cache_key("question", {"user_id": "u1", "pharmacy_id": 2})
    assert first != other_user
    assert first != other_pharmacy
