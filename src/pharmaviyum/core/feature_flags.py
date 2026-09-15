"""
Feature flag service for gradual rollouts and A/B testing
Best practice 2026: Redis-backed, segment targeting, percentage rollouts
"""

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from redis import asyncio as aioredis

from src.pharmaviyum.core.config import settings
from src.pharmaviyum.core.logging import get_logger

logger = get_logger(__name__)


class FlagType(str, Enum):
    """Feature flag types"""

    BOOLEAN = "boolean"  # Simple on/off
    PERCENTAGE = "percentage"  # Rollout to % of users
    SEGMENT = "segment"  # Target specific user segments
    MULTIVARIATE = "multivariate"  # A/B/n testing with variants


@dataclass
class FeatureFlag:
    """
    Feature flag definition

    Attributes:
        key: Unique flag identifier
        name: Human-readable name
        description: Flag description
        flag_type: Type of flag
        enabled: Global enable/disable
        percentage: Percentage rollout (0-100) for PERCENTAGE type
        segments: List of user segments for SEGMENT type
        variants: Dict of variant values for MULTIVARIATE type
        default_value: Default value when flag is disabled
        created_at: Creation timestamp
        updated_at: Last update timestamp
        created_by: User who created the flag
    """

    key: str
    name: str
    description: str = ""
    flag_type: FlagType = FlagType.BOOLEAN
    enabled: bool = False
    percentage: int = 0  # 0-100
    segments: list[str] = field(default_factory=list)
    variants: dict[str, Any] = field(default_factory=dict)
    default_value: Any = False
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    created_by: str = "system"

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "FeatureFlag":
        """Create from dictionary"""
        data["flag_type"] = FlagType(data["flag_type"])
        return cls(**data)


class FeatureFlagService:
    """
    Feature flag service with Redis backend

    Features:
    - Redis-backed storage for fast access
    - In-memory caching for performance
    - Percentage-based rollouts
    - Segment targeting
    - A/B testing with variants
    - Audit logging
    """

    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        """Initialize feature flag service"""
        self.redis = redis_client or aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        self.cache: dict[str, FeatureFlag] = {}
        self.cache_ttl = 60  # 1 minute cache

    async def get_flag(self, key: str) -> Optional[FeatureFlag]:
        """
        Get feature flag by key

        Args:
            key: Flag key

        Returns:
            FeatureFlag or None
        """
        # Check cache first
        if key in self.cache:
            return self.cache[key]

        # Fetch from Redis
        flag_json = await self.redis.get(f"feature_flag:{key}")
        if not flag_json:
            return None

        flag = FeatureFlag.from_dict(json.loads(flag_json))

        # Cache it
        self.cache[key] = flag

        return flag

    async def create_flag(self, flag: FeatureFlag) -> FeatureFlag:
        """
        Create a new feature flag

        Args:
            flag: Feature flag to create

        Returns:
            Created flag
        """
        # Check if flag already exists
        existing = await self.get_flag(flag.key)
        if existing:
            raise ValueError(f"Feature flag '{flag.key}' already exists")

        # Save to Redis
        await self.redis.set(
            f"feature_flag:{flag.key}",
            json.dumps(flag.to_dict(), ensure_ascii=False),
        )

        # Add to flags list
        await self.redis.sadd("feature_flags_list", flag.key)

        # Cache it
        self.cache[flag.key] = flag

        logger.info(f"Created feature flag: {flag.key}", extra={"flag": flag.to_dict()})

        return flag

    async def update_flag(self, key: str, updates: dict) -> FeatureFlag:
        """
        Update feature flag

        Args:
            key: Flag key
            updates: Dictionary of updates

        Returns:
            Updated flag
        """
        flag = await self.get_flag(key)
        if not flag:
            raise ValueError(f"Feature flag '{key}' not found")

        # Apply updates
        for field_name, value in updates.items():
            if hasattr(flag, field_name):
                setattr(flag, field_name, value)

        flag.updated_at = datetime.now(timezone.utc).isoformat()

        # Save to Redis
        await self.redis.set(
            f"feature_flag:{key}",
            json.dumps(flag.to_dict(), ensure_ascii=False),
        )

        # Update cache
        self.cache[key] = flag

        logger.info(f"Updated feature flag: {key}", extra={"updates": updates})

        return flag

    async def delete_flag(self, key: str) -> bool:
        """
        Delete feature flag

        Args:
            key: Flag key

        Returns:
            True if deleted
        """
        # Remove from Redis
        deleted = await self.redis.delete(f"feature_flag:{key}")

        # Remove from list
        await self.redis.srem("feature_flags_list", key)

        # Remove from cache
        self.cache.pop(key, None)

        if deleted:
            logger.info(f"Deleted feature flag: {key}")

        return deleted > 0

    async def list_flags(self) -> list[FeatureFlag]:
        """
        List all feature flags

        Returns:
            List of feature flags
        """
        keys = await self.redis.smembers("feature_flags_list")

        flags = []
        for key in keys:
            flag = await self.get_flag(key)
            if flag:
                flags.append(flag)

        return flags

    async def is_enabled(
        self,
        key: str,
        user_id: Optional[str] = None,
        user_segment: Optional[str] = None,
    ) -> bool:
        """
        Check if feature flag is enabled for user

        Args:
            key: Flag key
            user_id: User ID (for percentage/segment targeting)
            user_segment: User segment (for segment targeting)

        Returns:
            True if enabled
        """
        flag = await self.get_flag(key)
        if not flag:
            return False

        # Check if globally disabled
        if not flag.enabled:
            return False

        # Boolean flag - simple on/off
        if flag.flag_type == FlagType.BOOLEAN:
            return True

        # Percentage rollout
        if flag.flag_type == FlagType.PERCENTAGE:
            if not user_id:
                return False
            return self._check_percentage(flag.key, user_id, flag.percentage)

        # Segment targeting
        if flag.flag_type == FlagType.SEGMENT:
            if not user_segment:
                return False
            return user_segment in flag.segments

        # Multivariate (A/B testing)
        if flag.flag_type == FlagType.MULTIVARIATE:
            if not user_id:
                return False
            return True  # Will get variant via get_variant()

        return False

    async def get_variant(
        self,
        key: str,
        user_id: str,
    ) -> Any:
        """
        Get variant for multivariate flag (A/B testing)

        Args:
            key: Flag key
            user_id: User ID

        Returns:
            Variant value
        """
        flag = await self.get_flag(key)
        if not flag or not flag.enabled:
            return flag.default_value if flag else False

        if flag.flag_type != FlagType.MULTIVARIATE:
            return flag.default_value

        if not flag.variants:
            return flag.default_value

        # Deterministic variant assignment based on user_id
        variant_key = self._get_deterministic_key(flag.key, user_id)

        # Hash to get consistent bucket
        hash_value = int(hashlib.md5(variant_key.encode()).hexdigest(), 16)
        bucket = hash_value % 100

        # Distribute users across variants
        variant_names = list(flag.variants.keys())
        num_variants = len(variant_names)
        variant_index = bucket % num_variants

        selected_variant = variant_names[variant_index]

        logger.debug(
            "Variant assignment",
            extra={
                "flag": key,
                "user_id": user_id,
                "variant": selected_variant,
                "bucket": bucket,
            },
        )

        return flag.variants[selected_variant]

    def _check_percentage(self, key: str, user_id: str, percentage: int) -> bool:
        """
        Check if user is in percentage rollout

        Uses deterministic hashing for consistent assignment.
        """
        variant_key = self._get_deterministic_key(key, user_id)
        hash_value = int(hashlib.md5(variant_key.encode()).hexdigest(), 16)
        bucket = hash_value % 100

        return bucket < percentage

    def _get_deterministic_key(self, flag_key: str, user_id: str) -> str:
        """Generate deterministic key for consistent hashing"""
        return f"{flag_key}:{user_id}"

    async def get_flag_stats(self, key: str) -> dict:
        """
        Get statistics for a feature flag

        Args:
            key: Flag key

        Returns:
            Statistics dictionary
        """
        flag = await self.get_flag(key)
        if not flag:
            return {}

        # Get usage stats from Redis
        enabled_count = await self.redis.get(f"flag_stats:{key}:enabled") or 0
        disabled_count = await self.redis.get(f"flag_stats:{key}:disabled") or 0

        return {
            "flag_key": key,
            "enabled_count": int(enabled_count),
            "disabled_count": int(disabled_count),
            "total_checks": int(enabled_count) + int(disabled_count),
            "enabled_percentage": round(
                (
                    (
                        int(enabled_count)
                        / (int(enabled_count) + int(disabled_count))
                        * 100
                    )
                    if (int(enabled_count) + int(disabled_count)) > 0
                    else 0
                ),
                2,
            ),
        }

    async def record_check(self, key: str, enabled: bool) -> None:
        """
        Record feature flag check for statistics

        Args:
            key: Flag key
            enabled: Whether flag was enabled
        """
        stat_key = (
            f"flag_stats:{key}:enabled" if enabled else f"flag_stats:{key}:disabled"
        )
        await self.redis.incr(stat_key)

    def invalidate_cache(self, key: Optional[str] = None) -> None:
        """Invalidate flag cache"""
        if key:
            self.cache.pop(key, None)
        else:
            self.cache.clear()


# Singleton instance
feature_flag_service = FeatureFlagService()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


async def is_feature_enabled(
    key: str,
    user_id: Optional[str] = None,
    user_segment: Optional[str] = None,
) -> bool:
    """
    Check if feature is enabled

    Convenience function for use in code.

    Usage:
        if await is_feature_enabled("ai_recommendations", user_id="123"):
            # Show AI recommendations
    """
    return await feature_flag_service.is_enabled(key, user_id, user_segment)


async def get_feature_variant(key: str, user_id: str) -> Any:
    """
    Get feature variant for A/B testing

    Usage:
        variant = await get_feature_variant("checkout_flow", user_id="123")
        if variant == "new":
            # Show new checkout
    """
    return await feature_flag_service.get_variant(key, user_id)
