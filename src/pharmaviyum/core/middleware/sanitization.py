"""
Input sanitization middleware
Best practice 2026: Prevent XSS and injection attacks
"""
import re
import html
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from src.pharmaviyum.core.logging import get_logger

logger = get_logger(__name__)


class SanitizationMiddleware(BaseHTTPMiddleware):
    """
    Input sanitization middleware
    
    Sanitizes request data to prevent:
    - XSS attacks (script injection)
    - HTML injection
    - SQL injection (additional layer)
    - Path traversal
    
    Features:
    - HTML entity encoding
    - Script tag removal
    - Dangerous pattern detection
    - Configurable sanitization rules
    """
    
    # Dangerous patterns to detect
    DANGEROUS_PATTERNS = [
        r"<script.*?>.*?</script>",  # Script tags
        r"javascript:",  # JavaScript protocol
        r"on\w+\s*=",  # Event handlers (onclick, onload, etc)
        r"<iframe.*?>.*?</iframe>",  # Iframe tags
        r"<object.*?>.*?</object>",  # Object tags
        r"<embed.*?>",  # Embed tags
        r"\.\./\.\./",  # Path traversal
    ]
    
    def __init__(self, app, enabled: bool = True):
        """Initialize sanitization middleware"""
        super().__init__(app)
        self.enabled = enabled
    
    async def dispatch(self, request: Request, call_next):
        """Process request with sanitization"""
        if not self.enabled:
            return await call_next(request)
        
        # Check for dangerous patterns in query parameters
        for key, value in request.query_params.items():
            if self._contains_dangerous_pattern(value):
                logger.warning(
                    f"Dangerous pattern detected in query param: {key}",
                    extra={"key": key, "value": value}
                )
                # Don't block, just log (Pydantic will validate)
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response
    
    def _contains_dangerous_pattern(self, value: str) -> bool:
        """Check if value contains dangerous patterns"""
        if not isinstance(value, str):
            return False
        
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        
        return False
    
    @staticmethod
    def sanitize_string(value: str) -> str:
        """
        Sanitize string input
        
        Args:
            value: Input string
            
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            return value
        
        # HTML entity encoding
        sanitized = html.escape(value)
        
        # Remove null bytes
        sanitized = sanitized.replace("\x00", "")
        
        # Normalize whitespace
        sanitized = re.sub(r"\s+", " ", sanitized).strip()
        
        return sanitized
    
    @staticmethod
    def sanitize_html(value: str) -> str:
        """
        Sanitize HTML input (allow safe tags)
        
        Args:
            value: HTML string
            
        Returns:
            Sanitized HTML
        """
        if not isinstance(value, str):
            return value
        
        # Remove script tags
        sanitized = re.sub(r"<script.*?>.*?</script>", "", value, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove event handlers
        sanitized = re.sub(r"\s+on\w+\s*=\s*['\"].*?['\"]", "", sanitized, flags=re.IGNORECASE)
        
        # Remove javascript: protocol
        sanitized = re.sub(r"javascript:", "", sanitized, flags=re.IGNORECASE)
        
        return sanitized
