"""
Semantic Prompt Cache for Agent Harness.

Best practice 2026:
- Exact hash matching for identical queries (fastest)
- Semantic similarity matching for near-identical queries (saves LLM calls)
- Redis-backed with configurable TTL
- Asynchronous non-blocking operations
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from src.pharmaviyum.core.logging import logger


class PromptCache:
    """
    Production-ready prompt cache with exact and semantic matching.

    Prevents redundant LLM calls for:
    - Frequently asked questions (e.g., "What is the dosage of Paracetamol?")
    - Similar queries with minor wording differences
    """

    def __init__(
        self,
        redis_client,
        embeddings_provider=None,
        exact_ttl_seconds: int = 86400 * 7,  # 7 days for exact matches
        semantic_ttl_seconds: int = 86400 * 30,  # 30 days for semantic index
        similarity_threshold: float = 0.95,
    ):
        self.redis = redis_client
        self.embeddings = embeddings_provider
        self.exact_ttl = exact_ttl_seconds
        self.semantic_ttl = semantic_ttl_seconds
        self.similarity_threshold = similarity_threshold
        self._exact_prefix = "cache:prompt:exact"
        self._semantic_prefix = "cache:prompt:semantic"

    async def get(
        self, prompt: str, context: dict[str, Any] | None = None
    ) -> dict | None:
        """
        Retrieve cached response for a prompt.

        Priority:
        1. Exact hash match (O(1) Redis GET)
        2. Semantic similarity match (if embeddings provider is available)
        """
        self._require_authenticated_scope(context)
        cache_key = self._build_cache_key(prompt, context)

        # 1. Try exact match
        exact_key = f"{self._exact_prefix}:{cache_key}"
        cached = await self.redis.get(exact_key)
        if cached:
            logger.debug(f"Prompt cache HIT (exact): {cache_key[:16]}")
            return json.loads(cached)

        # 2. Try semantic match (if enabled and available)
        if self.embeddings:
            semantic_result = await self._semantic_search(prompt, context)
            if (
                semantic_result
                and semantic_result["score"] >= self.similarity_threshold
            ):
                logger.debug(
                    f"Prompt cache HIT (semantic, score={semantic_result['score']:.2f}): {cache_key[:16]}"
                )
                return semantic_result["response"]

        logger.debug(f"Prompt cache MISS: {cache_key[:16]}")
        return None

    async def set(
        self,
        prompt: str,
        response: dict,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Cache a prompt-response pair.

        Stores both exact hash and semantic embedding (if available).
        """
        self._require_authenticated_scope(context)
        cache_key = self._build_cache_key(prompt, context)

        # 1. Store exact match
        exact_key = f"{self._exact_prefix}:{cache_key}"
        await self.redis.setex(exact_key, self.exact_ttl, json.dumps(response))

        # 2. Store semantic embedding (async, non-blocking)
        if self.embeddings:
            try:
                embedding = await self.embeddings.embed(prompt)
                # Store in Redis sorted set for similarity search
                # Score = 1.0 (we'll calculate actual similarity at query time)
                semantic_key = f"{self._semantic_prefix}:{self._context_scope(context)}"
                payload = json.dumps(
                    {
                        "key": cache_key,
                        "prompt": prompt,
                        "response": response,
                        "embedding": embedding,
                    }
                )
                await self.redis.zadd(semantic_key, {payload: 1.0})
                await self.redis.expire(semantic_key, self.semantic_ttl)
            except Exception as e:
                logger.warning(f"Failed to cache semantic embedding: {e}")

    @staticmethod
    def _require_authenticated_scope(context: dict[str, Any] | None) -> None:
        """Reject cache operations that are not bound to one user and pharmacy."""
        user_id = context.get("user_id") if context else None
        pharmacy_id = context.get("pharmacy_id") if context else None
        if (
            user_id is None
            or not str(user_id).strip()
            or isinstance(pharmacy_id, bool)
            or not isinstance(pharmacy_id, int)
            or pharmacy_id <= 0
        ):
            raise ValueError(
                "Prompt cache requires an authenticated user and positive pharmacy_id"
            )

    @staticmethod
    def _context_scope(context: dict[str, Any] | None) -> str:
        """Keep semantic cache candidates isolated by authenticated tenant/user context."""
        if not context:
            return "anonymous"
        scoped = {
            key: context.get(key)
            for key in ("pharmacy_id", "user_id", "patient_id", "country", "language")
        }
        raw = json.dumps(scoped, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]

    def _build_cache_key(self, prompt: str, context: dict[str, Any] | None) -> str:
        """Generate a unique hash for the prompt + context."""
        context_str = json.dumps(context, sort_keys=True) if context else ""
        combined = f"{prompt}|{context_str}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()[:32]

    async def _semantic_search(
        self, prompt: str, context: dict[str, Any] | None = None
    ) -> dict | None:
        """
        Find semantically similar cached prompts.

        Note: For production scale, use a dedicated vector DB (like pgvector).
        For harness-level prompt caching, Redis ZSET with in-memory comparison is sufficient.
        """
        try:
            query_embedding = await self.embeddings.embed(prompt)

            # Get top 5 candidates from semantic cache
            semantic_key = f"{self._semantic_prefix}:{self._context_scope(context)}"
            candidates = await self.redis.zrevrange(
                semantic_key, 0, 4, withscores=False
            )

            import numpy as np

            best_match = None
            best_score = 0.0

            for candidate_json in candidates:
                candidate = json.loads(candidate_json)
                cand_embedding = candidate["embedding"]

                # Cosine similarity
                score = float(np.dot(query_embedding, cand_embedding))

                if score > best_score:
                    best_score = score
                    best_match = candidate

            if best_match and best_score >= self.similarity_threshold:
                return {
                    "score": best_score,
                    "response": best_match["response"],
                }

            return None

        except Exception as e:
            logger.warning(f"Semantic cache search failed: {e}")
            return None

    async def clear(self, pattern: str = "*") -> int:
        """Clear cache entries matching a pattern."""
        keys = await self.redis.keys(f"{self._exact_prefix}:{pattern}")
        if keys:
            return await self.redis.delete(*keys)
        return 0
