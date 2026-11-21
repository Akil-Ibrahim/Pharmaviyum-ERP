"""ERP integration endpoints.

This module provides a small adapter layer for ERP-related calls. In
production this would contain authentication, batching, and retry
logic when talking to external ERP services.
"""

from fastapi import APIRouter

from src.pharmaviyum.modules.auth.deps import CurrentSuperuser

router = APIRouter(prefix="/erp", tags=["ERP"])


@router.get("/status")
async def erp_status(_: CurrentSuperuser):
    """Lightweight status endpoint for the ERP integration.

    Returns a simple health object so external systems can verify
    connectivity. Replace with real checks when ERP is available.
    """
    # Placeholder implementation — extend with real checks as needed
    return {"status": "ok", "service": "erp", "reachable": False}


__all__ = ["router"]
