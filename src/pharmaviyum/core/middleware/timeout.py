"""
Request timeout middleware
Best practice 2026: Prevent hanging requests
"""
import asyncio
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from src.pharmaviyum.core.logging import get_logger

logger = get_logger(__name__)

DEFAULT_TIMEOUT = 30  # seconds


class TimeoutMiddleware(BaseHTTPMiddleware):
    """
    Request timeout middleware
    
    Prevents requests from hanging indefinitely.
    
    Features:
    - Configurable timeout per request
    - Graceful timeout handling
    - Logging of timeout events
    """
    
    def __init__(self, app, timeout: int = DEFAULT_TIMEOUT):
        """Initialize timeout middleware"""
        super().__init__(app)
        self.timeout = timeout
    
    async def dispatch(self, request: Request, call_next):
        """Process request with timeout"""
        try:
            # Create task for request processing
            response = await asyncio.wait_for(
                call_next(request),
                timeout=self.timeout,
            )
            return response
            
        except asyncio.TimeoutError:
            logger.error(
                f"Request timeout after {self.timeout}s",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "timeout": self.timeout,
                }
            )
            
            return JSONResponse(
                status_code=504,
                content={
                    "success": False,
                    "errors": [{
                        "code": "REQUEST_TIMEOUT",
                        "message": f"Request timed out after {self.timeout} seconds",
                    }],
                },
            )
