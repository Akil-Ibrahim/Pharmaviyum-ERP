"""
API v1 main router
Aggregates all endpoint routers
"""
from fastapi import APIRouter
from src.pharmaviyum.api.v1.endpoints import patients_router

api_router = APIRouter(prefix="/api/v1")

# Include all routers
api_router.include_router(patients_router)

__all__ = ["api_router"]
