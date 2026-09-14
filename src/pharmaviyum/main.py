"""
Pharmaviyum Main Application — FastAPI Entry Point.
"""
from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as aioredis

from src.pharmaviyum.api.v1 import api_v1_router
from src.pharmaviyum.api.middleware import RequestIDMiddleware, LoggingMiddleware
from src.pharmaviyum.api.exceptions import (
    pharmaviyum_api_error_handler,
    validation_exception_handler,
    general_exception_handler,
    PharmaviyumAPIError,
)
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from src.pharmaviyum.ai.dependencies import ai_container
from src.pharmaviyum.ai.config import settings
from src.pharmaviyum.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Pharmaviyum AI Application...")
    redis_client = None
    try:
        redis_client = aioredis.from_url(
            settings.redis.url, 
            decode_responses=True,
            health_check_interval=30,
        )
        await redis_client.ping()
        logger.info("✅ Redis connected")
        
        await ai_container.initialize(redis=redis_client, db_session_factory=None)
        logger.info("✅ AI Components initialized successfully")
        app.state.redis_client = redis_client
    except Exception as e:
        logger.error(f"❌ Failed to initialize AI components: {e}", exc_info=True)
    
    yield
    
    logger.info("🛑 Shutting down Pharmaviyum AI Application...")
    if redis_client:
        await redis_client.aclose()
        logger.info("✅ Redis connection closed")


app = FastAPI(
    title="Pharmaviyum AI API",
    description="Enterprise AI/LLM layer for pharmaceutical CRM.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# 1. Middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Exception Handlers
app.add_exception_handler(PharmaviyumAPIError, pharmaviyum_api_error_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 3. Routers
app.include_router(api_v1_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Pharmaviyum AI API is running",
        "version": "1.0.0",
        "documentation": "/docs",
        "metrics": "/metrics",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.pharmaviyum.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )
