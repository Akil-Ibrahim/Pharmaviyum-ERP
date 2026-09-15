"""
CORS Middleware Configuration
Best Practice: Never use allow_origins=["*"] with allow_credentials=True
This violates CORS specification and creates security vulnerabilities.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.pharmaviyum.config import settings


def setup_cors(app: FastAPI) -> None:
    """
    Configure CORS middleware with proper security settings.

    Best Practices:
    - Specify exact origins instead of wildcard (*)
    - Limit allowed methods to only what's needed
    - Restrict allowed headers to necessary ones
    - Use credentials only when required
    """
    app.add_middleware(
        CORSMiddleware,
        # ✅ GOOD: Specific origins from configuration
        # ❌ BAD: allow_origins=["*"] with credentials=True
        allow_origins=settings.ALLOWED_ORIGINS,
        # ✅ GOOD: Specific HTTP methods
        # ❌ BAD: allow_methods=["*"]
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        # ✅ GOOD: Specific headers
        # ❌ BAD: allow_headers=["*"]
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Accept",
            "Origin",
            "X-Requested-With",
        ],
        # ✅ GOOD: Allow credentials for authenticated requests
        allow_credentials=True,
        # ✅ GOOD: Pre-flight cache time (1 hour)
        max_age=3600,
        # ✅ GOOD: Expose headers for client access
        expose_headers=[
            "X-Request-ID",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
        ],
    )
