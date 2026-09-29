"""Idempotency middleware backed by the shared instrumented Redis client."""

import json

from fastapi import Request
from redis import asyncio as aioredis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.pharmaviyum.core.logging import get_logger
from src.pharmaviyum.redis_client import get_redis

logger = get_logger(__name__)

IDEMPOTENCY_KEY_HEADER = "Idempotency-Key"
IDEMPOTENCY_TTL = 86400


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Prevent duplicate state-changing requests during retries."""

    def __init__(self, app, redis_client: aioredis.Redis | None = None):
        super().__init__(app)
        self.redis = redis_client

    async def _client(self) -> aioredis.Redis:
        if self.redis is None:
            self.redis = await get_redis()
        return self.redis

    async def dispatch(self, request: Request, call_next):
        if request.method not in ["POST", "PUT", "PATCH"]:
            return await call_next(request)

        # POS transactions use database-backed, pharmacy-scoped idempotency.
        # Do not serve a Redis cache hit before the endpoint can validate the
        # tenant and request fingerprint.
        if request.url.path.endswith("/pos/transactions"):
            return await call_next(request)

        idempotency_key = request.headers.get(IDEMPOTENCY_KEY_HEADER)
        if not idempotency_key:
            return await call_next(request)

        if len(idempotency_key) > 255:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "errors": [
                        {
                            "code": "INVALID_IDEMPOTENCY_KEY",
                            "message": "Idempotency key too long (max 255 characters)",
                        }
                    ],
                },
            )

        redis = await self._client()
        redis_key = f"idempotency:{idempotency_key}"
        cached_response = await redis.get(redis_key)

        if cached_response:
            logger.info("Idempotency cache hit")
            cached_data = json.loads(cached_response)
            return JSONResponse(
                status_code=cached_data["status_code"],
                content=cached_data["body"],
                headers=cached_data.get("headers", {}),
            )

        response = await call_next(request)
        if not 200 <= response.status_code < 300:
            return response

        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        try:
            body_json = json.loads(response_body)
        except json.JSONDecodeError:
            body_json = {"raw": response_body.decode("utf-8", errors="ignore")}

        cache_data = {
            "status_code": response.status_code,
            "body": body_json,
            "headers": dict(response.headers),
        }
        await redis.setex(redis_key, IDEMPOTENCY_TTL, json.dumps(cache_data))
        logger.info("Cached idempotency response", extra={"ttl": IDEMPOTENCY_TTL})

        return JSONResponse(
            status_code=response.status_code,
            content=body_json,
            headers=dict(response.headers),
        )
