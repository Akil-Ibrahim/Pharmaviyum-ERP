"""Embeddings generation with Redis cache and local/cloud providers."""

from __future__ import annotations

import asyncio
import hashlib
from typing import Any, Protocol, cast

import numpy as np
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr


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
    ) -> None:
        self.model = model
        self.endpoint = endpoint
        self._dimensions = dimensions
        self._client: Any = None

    async def _get_client(self) -> Any:
        if self._client is None:
            try:
                import ollama

                self._client = ollama.AsyncClient(host=self.endpoint)
            except ImportError as exc:
                raise ImportError("Install ollama: pip install ollama") from exc
        return self._client

    async def embed(self, text: str) -> list[float]:
        client = await self._get_client()
        response: Any = await client.embeddings(model=self.model, prompt=text)
        return cast(list[float], response["embedding"])

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


class GeminiEmbeddingsProvider:
    """Cloud embeddings via Gemini at a fixed vector dimension."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-embedding-001",
        dimensions: int = 1024,
        batch_size: int = 32,
    ) -> None:
        self.model = model
        self._dimensions = dimensions
        self._batch_size = batch_size
        embeddings_cls: Any = GoogleGenerativeAIEmbeddings
        self._client = embeddings_cls(
            model=model,
            google_api_key=SecretStr(api_key),
            output_dimensionality=dimensions,
        )

    @staticmethod
    def _normalize(embedding: list[float]) -> list[float]:
        """Normalize reduced Gemini 001 vectors for cosine distance."""
        vector = np.asarray(embedding, dtype=np.float32)
        norm = float(np.linalg.norm(vector))
        if norm == 0.0:
            raise ValueError("Gemini embedding returned a zero vector")
        return (vector / norm).tolist()

    async def embed(self, text: str) -> list[float]:
        embedding = await self._client.aembed_query(text)
        return self._normalize(embedding)

    async def embed_batch(
        self, texts: list[str], batch_size: int = 32
    ) -> list[list[float]]:
        size = max(1, min(batch_size, self._batch_size))
        results: list[list[float]] = []
        for i in range(0, len(texts), size):
            embeddings = await self._client.aembed_documents(texts[i : i + size])
            results.extend(self._normalize(embedding) for embedding in embeddings)
        return results

    @property
    def dimensions(self) -> int:
        return self._dimensions


class OpenAIEmbeddingsProvider:
    """Cloud embeddings via OpenAI text-embedding-3-small at 1024 dimensions."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        dimensions: int = 1024,
        batch_size: int = 32,
    ) -> None:
        self.model = model
        self._dimensions = dimensions
        self._batch_size = batch_size
        self._client = OpenAIEmbeddings(
            model=model,
            dimensions=dimensions,
            api_key=SecretStr(api_key),
        )

    async def embed(self, text: str) -> list[float]:
        return await self._client.aembed_query(text)

    async def embed_batch(
        self, texts: list[str], batch_size: int = 32
    ) -> list[list[float]]:
        size = max(1, min(batch_size, self._batch_size))
        results: list[list[float]] = []
        for i in range(0, len(texts), size):
            results.extend(await self._client.aembed_documents(texts[i : i + size]))
        return results

    @property
    def dimensions(self) -> int:
        return self._dimensions


class CachedEmbeddings:
    """Embeddings with Redis cache (SHA256 key, 30-day TTL)."""

    def __init__(
        self,
        provider: EmbeddingsProvider,
        redis_client: Any,
        ttl: int = 86400 * 30,
        cache_namespace: str = "v2",
    ) -> None:
        self.provider = provider
        self.redis = redis_client
        self.ttl = ttl
        self._prefix = f"embeddings:{cache_namespace}:{provider.__class__.__name__}"

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
        provider: str = "ollama",
        use_cache: bool = True,
        redis_client: Any = None,
        api_key: str | None = None,
        model: str | None = None,
        endpoint: str = "http://localhost:11434",
        dimensions: int = 1024,
    ) -> EmbeddingsProvider:
        if provider == "ollama":
            base: EmbeddingsProvider = OllamaEmbeddings(
                model=model or "mxbai-embed-large",
                endpoint=endpoint,
                dimensions=dimensions,
            )
        elif provider == "gemini":
            if not api_key:
                raise RuntimeError(
                    "Gemini embeddings require GEMINI_API_KEY to be configured"
                )
            base = GeminiEmbeddingsProvider(
                api_key=api_key,
                model=model or "gemini-embedding-001",
                dimensions=dimensions,
            )
        elif provider == "openai":
            if not api_key:
                raise RuntimeError(
                    "OpenAI embeddings require OPENAI_API_KEY to be configured"
                )
            base = OpenAIEmbeddingsProvider(
                api_key=api_key,
                model=model or "text-embedding-3-small",
                dimensions=dimensions,
            )
        else:
            raise ValueError(f"Unknown embeddings provider: {provider}")

        return (
            CachedEmbeddings(base, redis_client) if use_cache and redis_client else base
        )
