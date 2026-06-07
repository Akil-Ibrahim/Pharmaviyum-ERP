"""API V1 router"""

from fastapi import APIRouter
from src.pharmaviyum.api.v1.endpoints import health
from src.pharmaviyum.api.v1 import users, products, orders

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(users.router)
api_router.include_router(products.router)
api_router.include_router(orders.router)
