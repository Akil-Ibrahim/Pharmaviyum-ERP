"""Pharmaviyum Main Application — FastAPI entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.pharmaviyum.ai.config import settings
from src.pharmaviyum.ai.dependencies import ai_container
from src.pharmaviyum.api.exceptions import (
    PharmaviyumAPIError,
    general_exception_handler,
    pharmaviyum_api_error_handler,
    validation_exception_handler,
)
from src.pharmaviyum.api.middleware import LoggingMiddleware, RequestIDMiddleware
from src.pharmaviyum.api.v1 import api_v1_router
from src.pharmaviyum.core.logging import logger
from src.pharmaviyum.core.static_files import setup_static_files
from src.pharmaviyum.database import AsyncSessionLocal
from src.pharmaviyum.redis_client import close_redis, get_redis
from src.pharmaviyum.observability.opentelemetry import (
    configure_opentelemetry,
    shutdown_opentelemetry,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize shared infrastructure once for the application lifetime."""
    logger.info("Starting Pharmaviyum AI Application")
    configure_opentelemetry(app)

    try:
        redis_client = await get_redis()
        app.state.redis_client = redis_client
        app.state.db_session_factory = AsyncSessionLocal

        await ai_container.initialize(
            redis=redis_client,
            db_session_factory=AsyncSessionLocal,
        )
        logger.info("Application dependencies initialized")
    except Exception:
        logger.exception("Failed to initialize critical application dependencies")
        if settings.environment == "production":
            shutdown_opentelemetry()
    await close_redis()
            raise

    yield

    logger.info("Shutting down Pharmaviyum AI Application")
    await close_redis()


app = FastAPI(
    title="Pharmaviyum AI API",
    description="Enterprise AI/LLM layer for pharmaceutical CRM.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

# Starlette wraps middleware in reverse registration order. RequestID must be
# registered last so it runs before LoggingMiddleware and the logger can always
# include the correlation ID for the request lifecycle.
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)

allowed_origins = settings.cors_origins
if settings.environment != "production" and not allowed_origins:
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=settings.environment != "production" or bool(allowed_origins),
    allow_methods=(
        ["*"]
        if settings.environment != "production"
        else ["GET", "POST", "PUT", "PATCH", "DELETE"]
    ),
    allow_headers=(
        ["*"]
        if settings.environment != "production"
        else ["Authorization", "Content-Type", "X-Request-ID"]
    ),
)


async def _handle_pharmaviyum_api_error(
    request: Request, exc: Exception
) -> JSONResponse:
    return await pharmaviyum_api_error_handler(request, cast(PharmaviyumAPIError, exc))


async def _handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
    return await validation_exception_handler(
        request, cast(RequestValidationError | ValidationError, exc)
    )


app.add_exception_handler(PharmaviyumAPIError, _handle_pharmaviyum_api_error)
app.add_exception_handler(RequestValidationError, _handle_validation_error)
app.add_exception_handler(ValidationError, _handle_validation_error)
app.add_exception_handler(Exception, general_exception_handler)
app.include_router(api_v1_router)


@app.get("/api-info", tags=["Root"])
async def root() -> dict[str, str]:
    return {
        "message": "Pharmaviyum AI API is running",
        "version": "1.0.0",
        "health": "/health",
        "metrics": "/metrics",
    }


# Serve the production React SPA from /app/static in Docker and from the
# repository frontend build directory during local development.
setup_static_files(app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.pharmaviyum.main:app",
        host="0.0.0.0",  # nosec B104: container must listen on all interfaces
        port=8000,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )
