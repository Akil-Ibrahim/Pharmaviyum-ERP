"""Feature flag service backed by the shared instrumented Redis client."""

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from redis import asyncio as aioredis

from src.pharmaviyum.core.logging import get_logger
from src.pharmaviyum.redis_client import get_redis

logger = get_logger(__name__)


class FlagType(str, Enum):
    BOOLEAN = "boolean"
    PERCENTAGE = "percentage"
    SEGMENT = "segment"
    MULTIVARIATE = "multivariate"


@dataclass
class FeatureFlag:
    key: str
    name: str
    description: str = ""
    flag_type: FlagType = FlagType.BOOLEAN
    enabled: bool = False
    percentage: int = 0
    segments: list[str] = field(default_factory=list)
    variants: dict[str, Any] = field(default_factory=dict)
    default_value: Any = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_by: str = "system"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "FeatureFlag":
        data["flag_type"] = FlagType(data["flag_type"])
        return cls(**data)


class FeatureFlagService:
    """Feature flag service with Redis persistence and local cache."""

    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        self.redis = redis_client
        self.cache: dict[str, FeatureFlag] = {}
        self.cache_ttl = 60

    async def _client(self) -> aioredis.Redis:
        if self.redis is None:
            self.redis = await get_redis()
        return self.redis

    async def get_flag(self, key: str) -> Optional[FeatureFlag]:
        if key in self.cache:
            return self.cache[key]
        redis = await self._client()
        flag_json = await redis.get(f"feature_flag:{key}")
        if not flag_json:
            return None
        flag = FeatureFlag.from_dict(json.loads(flag_json))
        self.cache[key] = flag
        return flag

    async def create_flag(self, flag: FeatureFlag) -> FeatureFlag:
        if await self.get_flag(flag.key):
            raise ValueError(f"Feature flag '{flag.key}' already exists")
        redis = await self._client()
        await redis.set(f"feature_flag:{flag.key}", json.dumps(flag.to_dict(), ensure_ascii=False))
        await redis.sadd("feature_flags_list", flag.key)
        self.cache[flag.key] = flag
        logger.info("Created feature flag", extra={"flag_key": flag.key})
        return flag

    async def update_flag(self, key: str, updates: dict) -> FeatureFlag:
        flag = await self.get_flag(key)
        if not flag:
            raise ValueError(f"Feature flag '{key}' not found")
        for field_name, value in updates.items():
            if hasattr(flag, field_name):
                setattr(flag, field_name, value)
        flag.updated_at = datetime.now(timezone.utc).isoformat()
        redis = await self._client()
        await redis.set(f"feature_flag:{key}", json.dumps(flag.to_dict(), ensure_ascii=False))
        self.cache[key] = flag
        logger.info("Updated feature flag", extra={"flag_key": key})
        return flag

    async def delete_flag(self, key: str) -> bool:
        redis = await self._client()
        deleted = await redis.delete(f"feature_flag:{key}")
        await redis.srem("feature_flags_list", key)
        self.cache.pop(key, None)
        if deleted:
            logger.info("Deleted feature flag", extra={"flag_key": key})
        return deleted > 0

    async def list_flags(self) -> list[FeatureFlag]:
        redis = await self._client()
        keys = await redis.smembers("feature_flags_list")
        flags = []
        for key in keys:
            flag = await self.get_flag(key)
            if flag:
                flags.append(flag)
        return flags

    async def is_enabled(self, key: str, user_id: Optional[str] = None, user_segment: Optional[str] = None) -> bool:
        flag = await self.get_flag(key)
        if not flag or not flag.enabled:
            return False
        if flag.flag_type == FlagType.BOOLEAN:
            return True
        if flag.flag_type == FlagType.PERCENTAGE:
            return bool(user_id and self._check_percentage(flag.key, user_id, flag.percentage))
        if flag.flag_type == FlagType.SEGMENT:
            return bool(user_segment and user_segment in flag.segments)
        if flag.flag_type == FlagType.MULTIVARIATE:
            return bool(user_id)
        return False

    async def get_variant(self, key: str, user_id: str) -> Any:
        flag = await self.get_flag(key)
        if not flag or not flag.enabled or flag.flag_type != FlagType.MULTIVARIATE or not flag.variants:
            return flag.default_value if flag else False
        variant_key = self._get_deterministic_key(flag.key, user_id)
        hash_value = int(hashlib.md5(variant_key.encode(), usedforsecurity=False).hexdigest(), 16)
        bucket = hash_value % 100
        variant_names = list(flag.variants.keys())
        selected_variant = variant_names[bucket % len(variant_names)]
        return flag.variants[selected_variant]

    def _check_percentage(self, key: str, user_id: str, percentage: int) -> bool:
        variant_key = self._get_deterministic_key(key, user_id)
        hash_value = int(hashlib.md5(variant_key.encode(), usedforsecurity=False).hexdigest(), 16)
        return (hash_value % 100) < percentage

    def _get_deterministic_key(self, flag_key: str, user_id: str) -> str:
        return f"{flag_key}:{user_id}"

    async def get_flag_stats(self, key: str) -> dict:
        if not await self.get_flag(key):
            return {}
        redis = await self._client()
        enabled_count = int(await redis.get(f"flag_stats:{key}:enabled") or 0)
        disabled_count = int(await redis.get(f"flag_stats:{key}:disabled") or 0)
        total = enabled_count + disabled_count
        return {
            "flag_key": key,
            "enabled_count": enabled_count,
            "disabled_count": disabled_count,
            "total_checks": total,
            "enabled_percentage": round(enabled_count / total * 100, 2) if total else 0,
        }

    async def record_check(self, key: str, enabled: bool) -> None:
        redis = await self._client()
        suffix = "enabled" if enabled else "disabled"
        await redis.incr(f"flag_stats:{key}:{suffix}")

    def invalidate_cache(self, key: Optional[str] = None) -> None:
        if key:
            self.cache.pop(key, None)
        else:
            self.cache.clear()


feature_flag_service = FeatureFlagService()


async def is_feature_enabled(key: str, user_id: Optional[str] = None, user_segment: Optional[str] = None) -> bool:
    return await feature_flag_service.is_enabled(key, user_id, user_segment)


async def get_feature_variant(key: str, user_id: str) -> Any:
    return await feature_flag_service.get_variant(key, user_id)
