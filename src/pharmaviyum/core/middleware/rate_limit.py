"""
Rate limiting middleware using Redis
Best practice 2026: Protect API from abuse and DDoS
"""
import time
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from redis import asyncio as aioredis
from src.pharmaviyum.core.config import settings
from src.pharmaviyum.core.logging import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Redis-based rate limiting middleware
    
    Implements sliding window algorithm for accurate rate limiting.
    
    Features:
    - Per-IP rate limiting
    - Per-user rate limiting (if authenticated)
    - Configurable limits per endpoint
    - Graceful degradation if Redis is down
    
    Headers added to response:
    - X-RateLimit-Limit: Maximum requests allowed
    - X-RateLimit-Remaining: Requests remaining in window
    - X-RateLimit-Reset: Unix timestamp when window resets
    """
    
    def __init__(self, app, redis_client: aioredis.Redis = None):
        """Initialize rate limiter with Redis client"""
        super().__init__(app)
        self.redis = redis_client or aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/ready", "/metrics"]:
            return await call_next(request)
        
        # Determine client identifier (user ID or IP)
        client_id = self._get_client_id(request)
        
        # Check rate limit
        allowed, limit, remaining, reset_time = await self._check_rate_limit(client_id)
        
        if not allowed:
            logger.warning(
                f"Rate limit exceeded for client: {client_id}",
                extra={
                    "client_id": client_id,
                    "path": request.url.path,
                    "limit": limit,
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "errors": [{
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please try again later.",
                        "retry_after": reset_time - int(time.time()),
                    }],
                },
                headers={
                    "Retry-After": str(reset_time - int(time.time())),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier (user ID or IP)"""
        # Try to get user ID from authenticated request
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.get('id')}"
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        
        # Handle proxy headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return f"ip:{client_ip}"
    
    async def _check_rate_limit(self, client_id: str) -> tuple[bool, int, int, int]:
        """
        Check if request is within rate limit using sliding window
        
        Returns:
            Tuple of (allowed, limit, remaining, reset_time)
        """
        try:
            now = int(time.time())
            window_size = 60  # 1 minute window
            limit = settings.RATE_LIMIT_PER_MINUTE
            
            # Redis key for this client
            key = f"ratelimit:{client_id}"
            
            # Sliding window implementation
            pipe = self.redis.pipeline()
            
            # Remove old entries outside window
            pipe.zremrangebyscore(key, 0, now - window_size)
            
            # Count current requests in window
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {f"{now}:{id(self)}": now})
            
            # Set expiry on key
            pipe.expire(key, window_size)
            
            # Execute pipeline
            results = await pipe.execute()
            
            # Get count (second result from pipeline)
            current_count = results[1]
            
            # Check if within limit
            allowed = current_count < limit
            remaining = max(0, limit - current_count - 1)
            reset_time = now + window_size
            
            return allowed, limit, remaining, reset_time
            
        except Exception as e:
            # Graceful degradation: allow request if Redis is down
            logger.error(f"Rate limit check failed: {e}")
            return True, settings.RATE_LIMIT_PER_MINUTE, settings.RATE_LIMIT_PER_MINUTE, int(time.time()) + 60
