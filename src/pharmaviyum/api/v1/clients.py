"""High-level client router for API v1.

This module re-exports the detailed endpoints defined under
`api.v1.endpoints.clients` to keep the top-level v1 package organized.
"""

from src.pharmaviyum.api.v1.endpoints import clients as clients_endpoints
from fastapi import APIRouter

router = APIRouter()

# Re-use the endpoints router implemented in endpoints/clients.py
router.include_router(clients_endpoints.router, prefix="/clients", tags=["Clients"])

__all__ = ["router"]
