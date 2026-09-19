"""API v1 Router Aggregation."""

from fastapi import APIRouter

from .ai import router as ai_router
from .auth import router as auth_router
from .ingestion import router as ingestion_router
from .monitoring import router as monitoring_router
from .orders import router as orders_router
from .patient_purchases import router as patient_purchases_router
from .pharmacy_entities import router as pharmacy_entities_router
from .products import router as products_router
from .users import router as users_router

api_v1_router = APIRouter()

api_v1_router.include_router(ai_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(ingestion_router)
api_v1_router.include_router(monitoring_router)
api_v1_router.include_router(orders_router)
api_v1_router.include_router(patient_purchases_router)
api_v1_router.include_router(pharmacy_entities_router)
api_v1_router.include_router(products_router)
api_v1_router.include_router(users_router)

__all__ = ["api_v1_router"]
