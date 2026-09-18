"""Authenticated patient API."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.pharmaviyum.core.database import get_db
from src.pharmaviyum.modules.auth.deps import (
    get_current_active_superuser,
    get_current_active_user,
)
from src.pharmaviyum.repositories.patient import PatientRepository
from src.pharmaviyum.schemas.patient import (
    PatientAIProfile,
    PatientCreate,
    PatientListResponse,
    PatientResponse,
    PatientUpdate,
)
from src.pharmaviyum.services.patient import PatientService

router = APIRouter(prefix="/patients", tags=["Patients"])


def get_patient_service(db: AsyncSession = Depends(get_db)) -> PatientService:
    return PatientService(PatientRepository(db))


@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    data: PatientCreate,
    service: PatientService = Depends(get_patient_service),
    _: object = Depends(get_current_active_superuser),
):
    try:
        patient = await service.create_patient(data=data, created_by=None)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return PatientResponse.model_validate(patient)


@router.get("/", response_model=list[PatientListResponse])
async def list_patients(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: str | None = Query(None),
    city: str | None = Query(None),
    country: str | None = Query(None),
    loyalty_tier: str | None = Query(None),
    is_active: bool | None = Query(None),
    service: PatientService = Depends(get_patient_service),
    _: object = Depends(get_current_active_user),
):
    patients, _ = await service.list_patients(
        query_text=search,
        city=city,
        country=country,
        loyalty_tier=loyalty_tier,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )
    return [PatientListResponse.model_validate(patient) for patient in patients]


@router.get("/statistics")
async def get_patient_statistics(
    service: PatientService = Depends(get_patient_service),
    _: object = Depends(get_current_active_user),
):
    return await service.get_statistics()


@router.get("/phone/{phone}", response_model=PatientResponse)
async def get_patient_by_phone(
    phone: str,
    service: PatientService = Depends(get_patient_service),
    _: object = Depends(get_current_active_user),
):
    patient = await service.get_patient_by_phone(phone)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientResponse.model_validate(patient)


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: int,
    service: PatientService = Depends(get_patient_service),
    _: object = Depends(get_current_active_user),
):
    patient = await service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientResponse.model_validate(patient)


@router.get("/{patient_id}/ai-profile", response_model=PatientAIProfile)
async def get_patient_ai_profile(
    patient_id: int,
    service: PatientService = Depends(get_patient_service),
    _: object = Depends(get_current_active_user),
):
    profile = await service.get_ai_profile(patient_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Patient not found")
    return profile


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    data: PatientUpdate,
    service: PatientService = Depends(get_patient_service),
    _: object = Depends(get_current_active_superuser),
):
    try:
        patient = await service.update_patient(
            id=patient_id, data=data, updated_by=None
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientResponse.model_validate(patient)


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: int,
    service: PatientService = Depends(get_patient_service),
    _: object = Depends(get_current_active_superuser),
):
    deleted = await service.delete_patient(
        id=patient_id, deleted_by=None, hard_delete=False
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Patient not found")
    return None


@router.post("/{patient_id}/visit", response_model=PatientResponse)
async def record_visit(
    patient_id: int,
    purchase_amount: int = Query(0, ge=0),
    service: PatientService = Depends(get_patient_service),
    _: object = Depends(get_current_active_user),
):
    patient = await service.record_visit(id=patient_id, purchase_amount=purchase_amount)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientResponse.model_validate(patient)
