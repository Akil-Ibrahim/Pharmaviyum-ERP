"""
Patient API endpoints
CRUD operations for patient management
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional
from src.pharmaviyum.core.database import get_db
from src.pharmaviyum.models.patients import Patient
from src.pharmaviyum.schemas.patient import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PatientListResponse,
)

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient_data: PatientCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new patient
    
    Args:
        patient_data: Patient creation data
        db: Database session
        
    Returns:
        Created patient object
        
    Raises:
        HTTPException 400: If phone already exists
    """
    # Check if phone already exists
    existing = await db.execute(
        select(Patient).where(Patient.phone == patient_data.phone)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient with this phone already exists"
        )
    
    # Create patient
    patient = Patient(
        **patient_data.model_dump(),
        full_name=f"{patient_data.first_name} {patient_data.last_name}",
    )
    db.add(patient)
    await db.flush()
    await db.refresh(patient)
    
    return patient


@router.get("/", response_model=list[PatientListResponse])
async def list_patients(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max records to return"),
    search: Optional[str] = Query(None, description="Search by name or phone"),
    city: Optional[str] = Query(None, description="Filter by city"),
    country: Optional[str] = Query(None, description="Filter by country"),
    loyalty_tier: Optional[str] = Query(None, description="Filter by loyalty tier"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
):
    """
    List patients with filtering and pagination
    
    Args:
        skip: Pagination offset
        limit: Pagination limit
        search: Search query (name or phone)
        city: City filter
        country: Country filter
        loyalty_tier: Loyalty tier filter
        is_active: Active status filter
        db: Database session
        
    Returns:
        List of patients
    """
    query = select(Patient)
    
    # Apply filters
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Patient.full_name.ilike(search_pattern),
                Patient.phone.ilike(search_pattern),
            )
        )
    if city:
        query = query.where(Patient.city == city)
    if country:
        query = query.where(Patient.country == country)
    if loyalty_tier:
        query = query.where(Patient.loyalty_tier == loyalty_tier)
    if is_active is not None:
        query = query.where(Patient.is_active == is_active)
    
    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(Patient.updated_at.desc())
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/count")
async def count_patients(
    is_active: Optional[bool] = Query(None),
    country: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Count patients with optional filters
    
    Returns:
        Dictionary with count
    """
    query = select(func.count(Patient.id))
    
    if is_active is not None:
        query = query.where(Patient.is_active == is_active)
    if country:
        query = query.where(Patient.country == country)
    
    result = await db.execute(query)
    return {"count": result.scalar_one()}


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get patient by ID
    
    Args:
        patient_id: Patient ID
        db: Database session
        
    Returns:
        Patient object
        
    Raises:
        HTTPException 404: If patient not found
    """
    result = await db.execute(
        select(Patient).where(Patient.id == patient_id)
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    return patient


@router.get("/phone/{phone}", response_model=PatientResponse)
async def get_patient_by_phone(
    phone: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get patient by phone number
    
    Args:
        phone: Patient phone number
        db: Database session
        
    Returns:
        Patient object
        
    Raises:
        HTTPException 404: If patient not found
    """
    result = await db.execute(
        select(Patient).where(Patient.phone == phone)
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    return patient


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    patient_data: PatientUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update patient data
    
    Args:
        patient_id: Patient ID
        patient_data: Update data (only provided fields)
        db: Database session
        
    Returns:
        Updated patient object
        
    Raises:
        HTTPException 404: If patient not found
    """
    result = await db.execute(
        select(Patient).where(Patient.id == patient_id)
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Update only provided fields
    update_data = patient_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)
    
    # Update full_name if first/last name changed
    if "first_name" in update_data or "last_name" in update_data:
        patient.full_name = f"{patient.first_name} {patient.last_name}"
    
    await db.flush()
    await db.refresh(patient)
    
    return patient


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete patient (soft delete - set is_active=False)
    
    Args:
        patient_id: Patient ID
        db: Database session
        
    Raises:
        HTTPException 404: If patient not found
    """
    result = await db.execute(
        select(Patient).where(Patient.id == patient_id)
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Soft delete
    patient.is_active = False
    await db.flush()
