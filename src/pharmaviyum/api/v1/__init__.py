"""API v1 Router Aggregation."""

from fastapi import APIRouter

from .ai import router as ai_router
from .ingestion import router as ingestion_router
from .monitoring import router as monitoring_router
from .pharmacy_entities import router as pharmacy_entities_router

api_v1_router = APIRouter()

api_v1_router.include_router(ai_router)
api_v1_router.include_router(ingestion_router)
api_v1_router.include_router(monitoring_router)
api_v1_router.include_router(pharmacy_entities_router)

__all__ = ["api_v1_router"]
