"""
Pharmaviyum CRM - Main FastAPI application
First AI-powered CRM for pharmacy retail in SEA
Best practice 2026 architecture
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.pharmaviyum.core.config import settings
from src.pharmaviyum.core.logging import setup_logging, get_logger
from src.pharmaviyum.core.telemetry import setup_telemetry
from src.pharmaviyum.core.middleware import (
    CorrelationIdMiddleware,
    AuditMiddleware,
    RateLimitMiddleware,
    IdempotencyMiddleware,
    SanitizationMiddleware,
    TimeoutMiddleware,
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
from src.pharmaviyum.api.v1.router import api_router


# Setup logging
setup_logging()
logger = get_logger(__name__)


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered CRM for pharmacy retail in Southeast Asia",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)


# Setup OpenTelemetry
setup_telemetry(app=app)


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

# 3. Idempotency
app.add_middleware(IdempotencyMiddleware)

# 4. Sanitization
app.add_middleware(SanitizationMiddleware)

# 5. Audit logging
app.add_middleware(AuditMiddleware)

# 6. Correlation ID
app.add_middleware(CorrelationIdMiddleware)

# 7. CORS (innermost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API router
app.include_router(api_router)


@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info(
        f"Starting {settings.APP_NAME} v{settings.APP_VERSION}",
        extra={"environment": settings.ENVIRONMENT.value}
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Shutting down application")


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT.value,
    }


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else "Disabled in production",
        "health": "/health",
    }
