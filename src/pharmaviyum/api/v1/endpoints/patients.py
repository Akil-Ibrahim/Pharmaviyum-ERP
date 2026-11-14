"""Authenticated patient API."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.pharmaviyum.core.database import get_db
from src.pharmaviyum.modules.auth.deps import (
    get_current_active_superuser,
    get_current_active_user,
)
from src.pharmaviyum.modules.auth.tenant import resolve_pharmacy_scope
from src.pharmaviyum.repositories.patient import PatientRepository
from src.pharmaviyum.schemas.patient import (
    PatientAIProfile,
    PatientCreate,
    PatientListResponse,
    PatientResponse,
    PatientUpdate,
)
from src.pharmaviyum.services.patient import PatientService

router = APIRouter(prefix="/api/v1/patients", tags=["Patients"])


def get_patient_service(db: AsyncSession = Depends(get_db)) -> PatientService:
    return PatientService(PatientRepository(db))


@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    data: PatientCreate,
    db: AsyncSession = Depends(get_db),
    service: PatientService = Depends(get_patient_service),
    current_user=Depends(get_current_active_superuser),
    pharmacy_id: int | None = Query(None, gt=0),
):
    try:
        scope = await resolve_pharmacy_scope(pharmacy_id, current_user, db)
        patient = await service.create_patient(
            data=data, created_by=None, pharmacy_id=scope
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return PatientResponse.model_validate(patient)


@router.get("/", response_model=list[PatientListResponse])
async def list_patients(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: str | None = Query(None),
    city: str | None = Query(None),
    country: str | None = Query(None),
    loyalty_tier: str | None = Query(None),
    is_active: bool | None = Query(None),
    service: PatientService = Depends(get_patient_service),
    current_user=Depends(get_current_active_user),
    pharmacy_id: int | None = Query(None, gt=0),
):
    scope = await resolve_pharmacy_scope(pharmacy_id, current_user, db)
    patients, _ = await service.list_patients(
        query_text=search,
        city=city,
        country=country,
        loyalty_tier=loyalty_tier,
        is_active=is_active,
        page=page,
        page_size=page_size,
        pharmacy_id=scope,
    )
    return [PatientListResponse.model_validate(patient) for patient in patients]


@router.get("/statistics")
async def get_patient_statistics(
    db: AsyncSession = Depends(get_db),
    service: PatientService = Depends(get_patient_service),
    current_user=Depends(get_current_active_user),
    pharmacy_id: int | None = Query(None, gt=0),
):
    scope = await resolve_pharmacy_scope(pharmacy_id, current_user, db)
    return await service.get_statistics(pharmacy_id=scope)


@router.get("/phone/{phone}", response_model=PatientResponse)
async def get_patient_by_phone(
    phone: str,
    db: AsyncSession = Depends(get_db),
    service: PatientService = Depends(get_patient_service),
    current_user=Depends(get_current_active_user),
    pharmacy_id: int | None = Query(None, gt=0),
):
    scope = await resolve_pharmacy_scope(pharmacy_id, current_user, db)
    patient = await service.get_patient_by_phone(phone, pharmacy_id=scope)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientResponse.model_validate(patient)


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    service: PatientService = Depends(get_patient_service),
    current_user=Depends(get_current_active_user),
    pharmacy_id: int | None = Query(None, gt=0),
):
    scope = await resolve_pharmacy_scope(pharmacy_id, current_user, db)
    patient = await service.get_patient(patient_id, pharmacy_id=scope)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientResponse.model_validate(patient)


@router.get("/{patient_id}/ai-profile", response_model=PatientAIProfile)
async def get_patient_ai_profile(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    service: PatientService = Depends(get_patient_service),
    current_user=Depends(get_current_active_user),
    pharmacy_id: int | None = Query(None, gt=0),
):
    scope = await resolve_pharmacy_scope(pharmacy_id, current_user, db)
    profile = await service.get_ai_profile(patient_id, pharmacy_id=scope)
    if not profile:
        raise HTTPException(status_code=404, detail="Patient not found")
    return profile


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    data: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    service: PatientService = Depends(get_patient_service),
    current_user=Depends(get_current_active_superuser),
    pharmacy_id: int | None = Query(None, gt=0),
):
    try:
        scope = await resolve_pharmacy_scope(pharmacy_id, current_user, db)
        patient = await service.update_patient(
            id=patient_id, data=data, updated_by=None, pharmacy_id=scope
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientResponse.model_validate(patient)


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    service: PatientService = Depends(get_patient_service),
    current_user=Depends(get_current_active_superuser),
    pharmacy_id: int | None = Query(None, gt=0),
):
    scope = await resolve_pharmacy_scope(pharmacy_id, current_user, db)
    deleted = await service.delete_patient(
        id=patient_id, deleted_by=None, hard_delete=False, pharmacy_id=scope
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Patient not found")
    return None


@router.post("/{patient_id}/visit", response_model=PatientResponse)
async def record_visit(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    purchase_amount: float = Query(
        0.0,
        ge=0,
        deprecated=True,
        description="Deprecated: purchases must be recorded through Orders.",
    ),
    service: PatientService = Depends(get_patient_service),
    current_user=Depends(get_current_active_user),
    pharmacy_id: int | None = Query(None, gt=0),
):
    del purchase_amount
    scope = await resolve_pharmacy_scope(pharmacy_id, current_user, db)
    patient = await service.record_visit(id=patient_id, pharmacy_id=scope)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientResponse.model_validate(patient)
