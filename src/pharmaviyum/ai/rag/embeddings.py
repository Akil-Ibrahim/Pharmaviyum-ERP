"""Embeddings generation with Redis cache and Ollama."""

from __future__ import annotations

import asyncio
import hashlib
from typing import Protocol

import numpy as np


class EmbeddingsProvider(Protocol):
    async def embed(self, text: str) -> list[float]: ...
    async def embed_batch(
        self, texts: list[str], batch_size: int = 32
    ) -> list[list[float]]: ...
    @property
    def dimensions(self) -> int: ...


class OllamaEmbeddings:
    """Local embeddings via Ollama (mxbai-embed-large, 1024 dims)."""

    def __init__(
        self,
        model: str = "mxbai-embed-large",
        endpoint: str = "http://localhost:11434",
        dimensions: int = 1024,
    ):
        self.model = model
        self.endpoint = endpoint
        self._dimensions = dimensions
        self._client = None

    async def _get_client(self):
        if self._client is None:
            try:
                import ollama

                self._client = ollama.AsyncClient(host=self.endpoint)
            except ImportError:
                raise ImportError("Install ollama: pip install ollama")
        return self._client

    async def embed(self, text: str) -> list[float]:
        client = await self._get_client()
        response = await client.embeddings(model=self.model, prompt=text)
        return response["embedding"]

    async def embed_batch(
        self, texts: list[str], batch_size: int = 32
    ) -> list[list[float]]:
        results: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_results = await asyncio.gather(*[self.embed(t) for t in batch])
            results.extend(batch_results)
        return results

    @property
    def dimensions(self) -> int:
        return self._dimensions


class CachedEmbeddings:
    """Embeddings with Redis cache (SHA256 key, 30-day TTL)."""

    def __init__(
        self, provider: EmbeddingsProvider, redis_client, ttl: int = 86400 * 30
    ):
        self.provider = provider
        self.redis = redis_client
        self.ttl = ttl
        self._prefix = "embeddings:v1"

    async def embed(self, text: str) -> list[float]:
        cache_key = self._cache_key(text)
        cached = await self.redis.get(f"{self._prefix}:{cache_key}")
        if cached:
            return self._deserialize(cached)
        embedding = await self.provider.embed(text)
        await self.redis.setex(
            f"{self._prefix}:{cache_key}", self.ttl, self._serialize(embedding)
        )
        return embedding

    async def embed_batch(
        self, texts: list[str], batch_size: int = 32
    ) -> list[list[float]]:
        results: list[list[float] | None] = [None] * len(texts)
        to_compute: list[tuple[int, str]] = []
        cache_keys = [f"{self._prefix}:{self._cache_key(t)}" for t in texts]
        cached_values = await self.redis.mget(cache_keys)

        for i, cached in enumerate(cached_values):
            if cached:
                results[i] = self._deserialize(cached)
            else:
                to_compute.append((i, texts[i]))

        if to_compute:
            texts_to_compute = [t for _, t in to_compute]
            computed = await self.provider.embed_batch(texts_to_compute, batch_size)
            pipe = self.redis.pipeline()
            for (idx, text), embedding in zip(to_compute, computed):
                results[idx] = embedding
                pipe.setex(
                    f"{self._prefix}:{self._cache_key(text)}",
                    self.ttl,
                    self._serialize(embedding),
                )
            await pipe.execute()

        return [r for r in results if r is not None]

    @property
    def dimensions(self) -> int:
        return self.provider.dimensions

    def _cache_key(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]

    def _serialize(self, embedding: list[float]) -> bytes:
        return np.array(embedding, dtype=np.float32).tobytes()

    def _deserialize(self, data: bytes) -> list[float]:
        return np.frombuffer(data, dtype=np.float32).tolist()


class EmbeddingsFactory:
    @staticmethod
    def create(
        provider: str = "ollama", use_cache: bool = True, redis_client=None
    ) -> EmbeddingsProvider:
        if provider == "ollama":
            base = OllamaEmbeddings()
        else:
            raise ValueError(f"Unknown provider: {provider}")
        return (
            CachedEmbeddings(base, redis_client) if use_cache and redis_client else base
        )
