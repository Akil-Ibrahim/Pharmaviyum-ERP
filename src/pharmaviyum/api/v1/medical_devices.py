"""Search API for official medical-device reference records."""

from fastapi import APIRouter, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from src.pharmaviyum.models.medical_device import (
    MedicalDevice,
    MedicalDeviceAuthorization,
    MedicalDeviceIdentifier,
)
from src.pharmaviyum.modules.auth.deps import CurrentUser, SessionDep
from src.pharmaviyum.schemas.medical_device import MedicalDeviceSearchResult

router = APIRouter(prefix="/medical-devices", tags=["Medical Devices"])


@router.get("/search", response_model=list[MedicalDeviceSearchResult])
async def search_medical_devices(
    db: SessionDep,
    _: CurrentUser,
    q: str = Query(..., min_length=2, max_length=160),
    limit: int = Query(20, ge=1, le=100),
    country: str | None = Query(None, min_length=2, max_length=2),
    status: str | None = Query(None, min_length=2, max_length=80),
) -> list[MedicalDeviceSearchResult]:
    """Search by device name, brand, model, manufacturer, UDI or licence ID."""
    term = f"%{q.strip()}%"
    stmt = (
        select(MedicalDevice)
        .outerjoin(
            MedicalDeviceIdentifier,
            MedicalDeviceIdentifier.medical_device_id == MedicalDevice.id,
        )
        .outerjoin(
            MedicalDeviceAuthorization,
            MedicalDeviceAuthorization.medical_device_id == MedicalDevice.id,
        )
        .options(
            selectinload(MedicalDevice.identifiers),
            selectinload(MedicalDevice.authorizations),
        )
        .where(
            or_(
                MedicalDevice.name.ilike(term),
                MedicalDevice.brand_name.ilike(term),
                MedicalDevice.model.ilike(term),
                MedicalDevice.manufacturer.ilike(term),
                MedicalDevice.device_type.ilike(term),
                MedicalDevice.intended_purpose.ilike(term),
                MedicalDevice.risk_class.ilike(term),
                MedicalDeviceIdentifier.identifier_value.ilike(term),
                MedicalDeviceAuthorization.authorization_id.ilike(term),
                MedicalDevice.source_record_id.ilike(term),
            )
        )
    )
    if country:
        stmt = stmt.where(MedicalDevice.country == country.upper())
    if status:
        stmt = stmt.where(MedicalDevice.regulatory_status.ilike(status.strip()))
    stmt = stmt.distinct().order_by(MedicalDevice.name.asc()).limit(limit)
    result = await db.execute(stmt)
    return [
        MedicalDeviceSearchResult.model_validate(device)
        for device in result.scalars().unique().all()
    ]
