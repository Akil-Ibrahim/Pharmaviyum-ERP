"""Prescription API endpoints.

This project previously referenced a prescription router that was not present in
this branch. Keep the router minimal but valid so the FastAPI app can import and
start under Python 3.14 without breaking the rest of the product surface.
"""

from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])


@router.get("/", summary="List prescriptions")
async def list_prescriptions():
    """Placeholder list endpoint for prescription routes."""
    return {"items": [], "total": 0}


@router.get("/{prescription_id}", summary="Get prescription by ID")
async def get_prescription(prescription_id: int):
    """Placeholder detail endpoint for prescription routes."""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Prescription {prescription_id} not found",
    )
