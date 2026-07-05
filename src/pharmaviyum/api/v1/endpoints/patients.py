"""
Patient API endpoints - Rewritten with 2026 best practices
Uses Service layer, Response Envelope, Pagination, RBAC, Feature Flags
"""
from fastapi import APIRouter, Depends, Query, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.pharmaviyum.core.database import get_db
from src.pharmaviyum.core.uow import UnitOfWork
from src.pharmaviyum.core.schemas import ResponseEnvelope, PaginatedResponse
from src.pharmaviyum.core.security.rbac import get_current_active_user, require_role
from src.pharmaviyum.core.feature_flags import is_feature_enabled
from src.pharmaviyum.repositories.patient import PatientRepository
from src.pharmaviyum.services.patient import PatientService
from src.pharmaviyum.schemas.patient import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PatientListResponse,
    PatientAIProfile,
)
from src.pharmaviyum.core.exceptions import NotFoundException, ConflictException
from src.pharmaviyum.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/patients", tags=["patients"])


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_patient_service(db: AsyncSession = Depends(get_db)) -> PatientService:
    """Dependency: Patient service with repository"""
    repository = PatientRepository(db)
    return PatientService(repository)


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post(
    "/",
    response_model=ResponseEnvelope[PatientResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create new patient",
    description="Create a new patient with validation and event emission",
)
async def create_patient(
    patient_data: PatientCreate,
    request: Request,
    service: PatientService = Depends(get_patient_service),
    current_user: dict = Depends(get_current_active_user),
):
    """
    Create a new patient
    
    - Validates phone/email uniqueness
    - Emits patient.created event
    - Records metrics
    - Requires authentication
    """
    try:
        patient = await service.create_patient(
            data=patient_data,
            created_by=current_user.get("sub"),
        )
        
        return ResponseEnvelope.success_response(
            data=PatientResponse.model_validate(patient),
            meta={
                "correlation_id": getattr(request.state, "correlation_id", None),
            },
        )
    
    except ValueError as e:
        raise ConflictException(str(e))


@router.get(
    "/",
    response_model=ResponseEnvelope[PaginatedResponse[PatientListResponse]],
    summary="List patients",
    description="List patients with filtering, search, and pagination",
)
async def list_patients(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    search: str = Query(None, description="Search by name, phone, or email"),
    city: str = Query(None, description="Filter by city"),
    country: str = Query(None, description="Filter by country"),
    loyalty_tier: str = Query(None, description="Filter by loyalty tier"),
    is_active: bool = Query(None, description="Filter by active status"),
    service: PatientService = Depends(get_patient_service),
    current_user: dict = Depends(get_current_active_user),
):
    """
    List patients with advanced filtering
    
    - Supports text search
    - Multiple filter options
    - Pagination with metadata
    - Requires authentication
    """
    patients, total = await service.list_patients(
        query_text=search,
        city=city,
        country=country,
        loyalty_tier=loyalty_tier,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )
    
    paginated = PaginatedResponse.create(
        items=[PatientListResponse.model_validate(p) for p in patients],
        page=page,
        page_size=page_size,
        total_items=total,
    )
    
    return ResponseEnvelope.success_response(
        data=paginated,
        meta={
            "correlation_id": getattr(request.state, "correlation_id", None),
        },
    )


@router.get(
    "/statistics",
    response_model=ResponseEnvelope[dict],
    summary="Get patient statistics",
    description="Get aggregated patient statistics",
)
@require_role("manager")
async def get_patient_statistics(
    request: Request,
    service: PatientService = Depends(get_patient_service),
    current_user: dict = Depends(get_current_active_user),
):
    """
    Get patient statistics
    
    - Total/active/inactive counts
    - Breakdown by loyalty tier
    - Breakdown by country
    - Requires manager role
    """
    stats = await service.get_statistics()
    
    return ResponseEnvelope.success_response(
        data=stats,
        meta={
            "correlation_id": getattr(request.state, "correlation_id", None),
        },
    )


@router.get(
    "/phone/{phone}",
    response_model=ResponseEnvelope[PatientResponse],
    summary="Get patient by phone",
    description="Get patient by phone number with caching",
)
async def get_patient_by_phone(
    phone: str,
    request: Request,
    service: PatientService = Depends(get_patient_service),
    current_user: dict = Depends(get_current_active_user),
):
    """
    Get patient by phone number
    
    - Uses cache for performance
    - Requires authentication
    """
    patient = await service.get_patient_by_phone(phone)
    
    if not patient:
        raise NotFoundException("Patient", phone)
    
    return ResponseEnvelope.success_response(
        data=PatientResponse.model_validate(patient),
        meta={
            "correlation_id": getattr(request.state, "correlation_id", None),
            "cached": True,  # Indicate if from cache
        },
    )


@router.get(
    "/{patient_id}",
    response_model=ResponseEnvelope[PatientResponse],
    summary="Get patient by ID",
    description="Get patient by ID with all relationships",
)
async def get_patient(
    patient_id: int,
    request: Request,
    service: PatientService = Depends(get_patient_service),
    current_user: dict = Depends(get_current_active_user),
):
    """
    Get patient by ID
    
    - Includes allergies, conditions, insurances
    - Uses cache
    - Requires authentication
    """
    patient = await service.get_patient(patient_id)
    
    if not patient:
        raise NotFoundException("Patient", patient_id)
    
    return ResponseEnvelope.success_response(
        data=PatientResponse.model_validate(patient),
        meta={
            "correlation_id": getattr(request.state, "correlation_id", None),
        },
    )


@router.get(
    "/{patient_id}/ai-profile",
    response_model=ResponseEnvelope[PatientAIProfile],
    summary="Get AI-optimized patient profile",
    description="Get patient profile optimized for Mortarium AI",
)
async def get_patient_ai_profile(
    patient_id: int,
    request: Request,
    service: PatientService = Depends(get_patient_service),
    current_user: dict = Depends(get_current_active_user),
):
    """
    Get AI-optimized patient profile for Mortarium
    
    - Controlled by feature flag: ai_patient_profiles
    - Includes allergies, conditions
    - Optimized for AI context
    - Requires authentication
    """
    # Check feature flag
    if not await is_feature_enabled("ai_patient_profiles", user_id=current_user.get("sub")):
        raise NotFoundException("AI profile feature", "disabled")
    
    profile = await service.get_ai_profile(patient_id)
    
    if not profile:
        raise NotFoundException("Patient", patient_id)
    
    return ResponseEnvelope.success_response(
        data=profile,
        meta={
            "correlation_id": getattr(request.state, "correlation_id", None),
            "feature_flag": "ai_patient_profiles",
        },
    )


@router.put(
    "/{patient_id}",
    response_model=ResponseEnvelope[PatientResponse],
    summary="Update patient",
    description="Update patient with validation and event emission",
)
async def update_patient(
    patient_id: int,
    patient_data: PatientUpdate,
    request: Request,
    service: PatientService = Depends(get_patient_service),
    current_user: dict = Depends(get_current_active_user),
):
    """
    Update patient
    
    - Validates uniqueness constraints
    - Emits patient.updated event
    - Invalidates cache
    - Requires authentication
    """
    try:
        patient = await service.update_patient(
            id=patient_id,
            data=patient_data,
            updated_by=current_user.get("sub"),
        )
        
        if not patient:
            raise NotFoundException("Patient", patient_id)
        
        return ResponseEnvelope.success_response(
            data=PatientResponse.model_validate(patient),
            meta={
                "correlation_id": getattr(request.state, "correlation_id", None),
            },
        )
    
    except ValueError as e:
        raise ConflictException(str(e))


@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete patient",
    description="Soft delete patient (or hard delete with feature flag)",
)
async def delete_patient(
    patient_id: int,
    request: Request,
    hard_delete: bool = Query(False, description="Hard delete (requires feature flag)"),
    service: PatientService = Depends(get_patient_service),
    current_user: dict = Depends(get_current_active_user),
):
    """
    Delete patient
    
    - Default: soft delete (is_active=False)
    - Hard delete requires feature flag: patient_hard_delete
    - Emits patient.deleted event
    - Requires authentication
    """
    deleted = await service.delete_patient(
        id=patient_id,
        deleted_by=current_user.get("sub"),
        hard_delete=hard_delete,
    )
    
    if not deleted:
        raise NotFoundException("Patient", patient_id)
    
    return None


@router.post(
    "/{patient_id}/visit",
    response_model=ResponseEnvelope[PatientResponse],
    summary="Record patient visit",
    description="Record patient visit and update statistics",
)
async def record_visit(
    patient_id: int,
    request: Request,
    purchase_amount: int = Query(0, ge=0, description="Purchase amount"),
    service: PatientService = Depends(get_patient_service),
    current_user: dict = Depends(get_current_active_user),
):
    """
    Record patient visit
    
    - Updates visit_count
    - Updates total_purchases
    - Updates last_visit_date
    - Emits patient.visit_recorded event
    """
    patient = await service.record_visit(
        id=patient_id,
        purchase_amount=purchase_amount,
    )
    
    if not patient:
        raise NotFoundException("Patient", patient_id)
    
    return ResponseEnvelope.success_response(
        data=PatientResponse.model_validate(patient),
        meta={
            "correlation_id": getattr(request.state, "correlation_id", None),
        },
    )
