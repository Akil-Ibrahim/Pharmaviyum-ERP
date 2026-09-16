"""Rate limiting middleware using the shared instrumented Redis client."""

import time

from fastapi import Request, status
from redis import asyncio as aioredis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.pharmaviyum.core.config import settings
from src.pharmaviyum.core.logging import get_logger
from src.pharmaviyum.redis_client import get_redis

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-based sliding-window rate limiter."""

    def __init__(self, app, redis_client: aioredis.Redis = None):
        super().__init__(app)
        self.redis = redis_client

    async def _client(self) -> aioredis.Redis:
        if self.redis is None:
            self.redis = await get_redis()
        return self.redis

    async def dispatch(self, request: Request, call_next):
        if request.url.path in ["/health", "/ready", "/metrics"]:
            return await call_next(request)

        client_id = self._get_client_id(request)
        allowed, limit, remaining, reset_time = await self._check_rate_limit(client_id)

        if not allowed:
            logger.warning(
                "Rate limit exceeded",
                extra={"limit": limit, "path": request.scope.get("path", "")},
            )
            retry_after = max(reset_time - int(time.time()), 0)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "errors": [{
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please try again later.",
                        "retry_after": retry_after,
                    }],
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        return response

    def _get_client_id(self, request: Request) -> str:
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.get('id')}"
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        return f"ip:{client_ip}"

    async def _check_rate_limit(self, client_id: str) -> tuple[bool, int, int, int]:
        try:
            now = int(time.time())
            window_size = 60
            limit = settings.RATE_LIMIT_PER_MINUTE
            key = f"ratelimit:{client_id}"
            redis = await self._client()
            pipe = redis.pipeline()
            pipe.zremrangebyscore(key, 0, now - window_size)
            pipe.zcard(key)
            pipe.zadd(key, {f"{now}:{id(self)}": now})
            pipe.expire(key, window_size)
            results = await pipe.execute()
            current_count = results[1]
            allowed = current_count < limit
            remaining = max(0, limit - current_count - 1)
            return allowed, limit, remaining, now + window_size
        except Exception as exc:
            logger.error("Rate limit check failed", extra={"error": type(exc).__name__})
            return True, settings.RATE_LIMIT_PER_MINUTE, settings.RATE_LIMIT_PER_MINUTE, int(time.time()) + 60
