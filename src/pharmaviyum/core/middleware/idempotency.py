"""
Idempotency middleware for safe retries
Best practice 2026: Prevent duplicate operations on network retries
"""
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from redis import asyncio as aioredis
from src.pharmaviyum.core.config import settings
from src.pharmaviyum.core.logging import get_logger

logger = get_logger(__name__)

IDEMPOTENCY_KEY_HEADER = "Idempotency-Key"
IDEMPOTENCY_TTL = 86400  # 24 hours


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Idempotency middleware for POST/PUT/PATCH requests
    
    Ensures that retrying the same request doesn't create duplicate resources.
    
    How it works:
    1. Client sends request with Idempotency-Key header
    2. Middleware checks if key exists in Redis
    3. If exists: return cached response
    4. If not: process request and cache response
    
    Usage:
        POST /api/v1/patients
        Headers: Idempotency-Key: unique-request-id-123
    """
    
    def __init__(self, app, redis_client: aioredis.Redis = None):
        """Initialize idempotency middleware"""
        super().__init__(app)
        self.redis = redis_client or aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    
    async def dispatch(self, request: Request, call_next):
        """Process request with idempotency check"""
        # Only apply to state-changing methods
        if request.method not in ["POST", "PUT", "PATCH"]:
            return await call_next(request)
        
        # Get idempotency key from header
        idempotency_key = request.headers.get(IDEMPOTENCY_KEY_HEADER)
        
        if not idempotency_key:
            # No key provided - process normally
            return await call_next(request)
        
        # Validate key format (UUID or custom string)
        if len(idempotency_key) > 255:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "errors": [{
                        "code": "INVALID_IDEMPOTENCY_KEY",
                        "message": "Idempotency key too long (max 255 characters)",
                    }],
                }
            )
        
        # Create Redis key
        redis_key = f"idempotency:{idempotency_key}"
        
        # Check if request was already processed
        cached_response = await self.redis.get(redis_key)
        
        if cached_response:
            # Return cached response
            logger.info(
                f"Idempotency hit: returning cached response",
                extra={"idempotency_key": idempotency_key}
            )
            
            import json
            cached_data = json.loads(cached_response)
            
            return JSONResponse(
                status_code=cached_data["status_code"],
                content=cached_data["body"],
                headers=cached_data.get("headers", {}),
            )
        
        # Process request
        response = await call_next(request)
        
        # Cache successful responses (2xx status codes)
        if 200 <= response.status_code < 300:
            # Read response body
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            # Parse JSON response
            import json
            try:
                body_json = json.loads(response_body)
            except json.JSONDecodeError:
                body_json = {"raw": response_body.decode("utf-8", errors="ignore")}
            
            # Cache response
            cache_data = {
                "status_code": response.status_code,
                "body": body_json,
                "headers": dict(response.headers),
            }
            
            await self.redis.setex(
                redis_key,
                IDEMPOTENCY_TTL,
                json.dumps(cache_data),
            )
            
            logger.info(
                f"Cached idempotency response",
                extra={
                    "idempotency_key": idempotency_key,
                    "ttl": IDEMPOTENCY_TTL,
                }
            )
            
            # Return new response with cached body
            return JSONResponse(
                status_code=response.status_code,
                content=body_json,
                headers=dict(response.headers),
            )
        
        # Return original response for non-2xx
        return response
