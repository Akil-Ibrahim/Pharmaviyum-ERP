"""Pharmaviyum Main Application — FastAPI entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
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
from src.pharmaviyum.database import AsyncSessionLocal
from src.pharmaviyum.redis_client import close_redis, get_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize shared infrastructure once for the application lifetime."""
    logger.info("Starting Pharmaviyum AI Application")

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

app.add_exception_handler(PharmaviyumAPIError, pharmaviyum_api_error_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)
app.include_router(api_v1_router)


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    return {
        "message": "Pharmaviyum AI API is running",
        "version": "1.0.0",
        "health": "/health",
        "metrics": "/metrics",
    }


# FastAPI Cloud can serve the built React SPA from the same deployment. The
# path is resolved from this module instead of relying on the process CWD,
# while check_dir="auto" keeps local API-only development working before a
# frontend build has been produced.
frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
app.frontend("/", directory=frontend_dist, check_dir="auto")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.pharmaviyum.main:app",
        host="0.0.0.0",  # nosec B104: container must listen on all interfaces
        port=8000,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )
