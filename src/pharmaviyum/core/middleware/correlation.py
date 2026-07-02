"""
Correlation ID middleware for request tracing
Best practice 2026: Distributed tracing across services
"""
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from src.pharmaviyum.core.logging import get_logger

logger = get_logger(__name__)

CORRELATION_ID_HEADER = "X-Correlation-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add correlation ID to requests
    
    - Generates new correlation ID if not present
    - Adds to request state for logging
    - Adds to response headers for client tracking
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request"""
        # Get or generate correlation ID
        correlation_id = request.headers.get(CORRELATION_ID_HEADER)
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Add to request state
        request.state.correlation_id = correlation_id
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        
        return response
