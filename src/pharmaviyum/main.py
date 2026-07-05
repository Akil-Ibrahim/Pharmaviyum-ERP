"""
Pharmaviyum CRM - Main FastAPI application
First AI-powered CRM for pharmacy retail in SEA
Best practice 2026 architecture with feature flags
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.pharmaviyum.core.config import settings
from src.pharmaviyum.core.lifecycle import lifespan
from src.pharmaviyum.core.middleware import (
    CorrelationIdMiddleware,
    AuditMiddleware,
    RateLimitMiddleware,
    IdempotencyMiddleware,
    SanitizationMiddleware,
    TimeoutMiddleware,
    MetricsMiddleware,
    FeatureFlagMiddleware,
)
from src.pharmaviyum.core.exceptions import (
    PharmaviyumException,
    pharmaviyum_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    integrity_error_handler,
    sqlalchemy_error_handler,
    generic_exception_handler,
)
from src.pharmaviyum.api.v1.router import api_router, system_router


# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered CRM for pharmacy retail in Southeast Asia",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)


# Register exception handlers
app.add_exception_handler(PharmaviyumException, pharmaviyum_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# Add middleware (order matters - last added = first executed)
# 1. Timeout (outermost)
app.add_middleware(TimeoutMiddleware, timeout=30)

# 2. Rate limiting
app.add_middleware(RateLimitMiddleware)

# 3. Metrics (before idempotency to capture all requests)
app.add_middleware(MetricsMiddleware)

# 4. Feature flags (inject into request context)
app.add_middleware(FeatureFlagMiddleware)

# 5. Idempotency
app.add_middleware(IdempotencyMiddleware)

# 6. Sanitization
app.add_middleware(SanitizationMiddleware)

# 7. Audit logging
app.add_middleware(AuditMiddleware)

# 8. Correlation ID
app.add_middleware(CorrelationIdMiddleware)

# 9. CORS (innermost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(system_router)  # /health, /ready, /metrics, /debug
app.include_router(api_router)     # /api/v1/...


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else "Disabled in production",
        "health": "/health",
        "ready": "/ready",
        "metrics": "/metrics",
        "feature_flags": "/api/v1/feature-flags",
    }
