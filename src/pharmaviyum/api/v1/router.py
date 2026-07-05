"""
API v1 main router
Aggregates all endpoint routers
"""
from fastapi import APIRouter
from src.pharmaviyum.api.v1.endpoints import (
    patients_router,
    prescriptions_router,
)
from src.pharmaviyum.api.v1.endpoints.health import router as health_router
from src.pharmaviyum.api.v1.endpoints.debug import router as debug_router
from src.pharmaviyum.api.v1.endpoints.feature_flags import router as feature_flags_router

api_router = APIRouter(prefix="/api/v1")

# Business routers
api_router.include_router(patients_router)
api_router.include_router(prescriptions_router)
api_router.include_router(feature_flags_router)

# System routers (health, debug) - no /api/v1 prefix
system_router = APIRouter()
system_router.include_router(health_router)
system_router.include_router(debug_router)

__all__ = ["api_router", "system_router"]
