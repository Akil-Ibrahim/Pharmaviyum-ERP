"""
Patient service - Business logic layer
Best practice 2026: Service pattern with events, caching, feature flags
"""

from typing import Optional

from src.pharmaviyum.core.feature_flags import is_feature_enabled
from src.pharmaviyum.core.logging import get_logger
from src.pharmaviyum.core.metrics import (
    CACHE_HITS_TOTAL,
    CACHE_MISSES_TOTAL,
    PATIENTS_CREATED_TOTAL,
)
from src.pharmaviyum.models.patients import Patient
from src.pharmaviyum.repositories.patient import PatientRepository
from src.pharmaviyum.schemas.patient import PatientCreate, PatientUpdate
from src.pharmaviyum.services.cache import cache_service
from src.pharmaviyum.services.event_bus import Event, event_bus

logger = get_logger(__name__)


class PatientService:
    """
    Patient service with business logic

    Responsibilities:
    - Business rules validation
    - Cache management
    - Event emission
    - Feature flag checks
    - Metrics collection
    - Orchestration of repositories
    """

    def __init__(self, repository: PatientRepository):
        """
        Initialize service with repository

        Args:
            repository: Patient repository instance
        """
        self.repository = repository
        self.cache_ttl = 3600  # 1 hour

    async def create_patient(
        self,
        data: PatientCreate,
        created_by: Optional[str] = None,
    ) -> Patient:
        """
        Create new patient with business rules

        Args:
            data: Patient creation data
            created_by: User who created (for audit)

        Returns:
            Created patient

        Raises:
            ValueError: If validation fails
        """
        # Business rule: Check for duplicate phone
        existing = await self.repository.get_by_phone(data.phone)
        if existing:
            raise ValueError(f"Patient with phone {data.phone} already exists")

        # Business rule: Check for duplicate email (if provided)
        if data.email:
            existing = await self.repository.get_by_email(data.email)
            if existing:
                raise ValueError(f"Patient with email {data.email} already exists")

        # Create patient entity
        patient = Patient(
            **data.model_dump(),
            full_name=f"{data.first_name} {data.last_name}",
        )

        # Save to database
        patient = await self.repository.create(patient)

        # Record metrics
        PATIENTS_CREATED_TOTAL.labels(country=patient.country).inc()

        # Emit event (async, non-blocking)
        await event_bus.emit(
            Event(
                event_type="patient.created",
                data={
                    "patient_id": patient.id,
                    "full_name": patient.full_name,
                    "phone": patient.phone,
                    "country": patient.country,
                    "created_by": created_by,
                },
            )
        )

        logger.info(
            f"Created patient {patient.id}",
            extra={
                "patient_id": patient.id,
                "full_name": patient.full_name,
                "created_by": created_by,
            },
        )

        return patient

    async def get_patient(
        self,
        id: int,
        use_cache: bool = True,
    ) -> Optional[Patient]:
        """
        Get patient by ID with caching

        Args:
            id: Patient ID
            use_cache: Whether to use cache

        Returns:
            Patient or None
        """
        cache_key = f"patient:{id}"

        # Try cache first
        if use_cache:
            cached = await cache_service.get(cache_key)
            if cached:
                CACHE_HITS_TOTAL.labels(cache_type="patient").inc()
                logger.debug(f"Cache hit for patient {id}")
                return cached

        CACHE_MISSES_TOTAL.labels(cache_type="patient").inc()

        # Fetch from database
        patient = await self.repository.get_by_id_with_relations(id)

        # Cache result
        if patient and use_cache:
            await cache_service.set(cache_key, patient, ttl=self.cache_ttl)

        return patient

    async def get_patient_by_phone(self, phone: str) -> Optional[Patient]:
        """
        Get patient by phone with caching

        Args:
            phone: Phone number

        Returns:
            Patient or None
        """
        cache_key = f"patient:phone:{phone}"

        # Try cache
        cached = await cache_service.get(cache_key)
        if cached:
            CACHE_HITS_TOTAL.labels(cache_type="patient_phone").inc()
            return cached

        CACHE_MISSES_TOTAL.labels(cache_type="patient_phone").inc()

        # Fetch from database
        patient = await self.repository.get_by_phone(phone)

        # Cache result
        if patient:
            await cache_service.set(cache_key, patient, ttl=self.cache_ttl)

        return patient

    async def list_patients(
        self,
        query_text: Optional[str] = None,
        city: Optional[str] = None,
        country: Optional[str] = None,
        loyalty_tier: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Patient], int]:
        """
        List patients with filtering and pagination

        Args:
            query_text: Search query
            city: City filter
            country: Country filter
            loyalty_tier: Loyalty tier filter
            is_active: Active status filter
            page: Page number (1-based)
            page_size: Items per page

        Returns:
            Tuple of (patients, total_count)
        """
        skip = (page - 1) * page_size

        return await self.repository.search(
            query_text=query_text,
            city=city,
            country=country,
            loyalty_tier=loyalty_tier,
            is_active=is_active,
            skip=skip,
            limit=page_size,
        )

    async def update_patient(
        self,
        id: int,
        data: PatientUpdate,
        updated_by: Optional[str] = None,
    ) -> Optional[Patient]:
        """
        Update patient with business rules

        Args:
            id: Patient ID
            data: Update data
            updated_by: User who updated

        Returns:
            Updated patient or None

        Raises:
            ValueError: If validation fails
        """
        patient = await self.get_patient(id, use_cache=False)
        if not patient:
            return None

        # Business rule: Check for duplicate phone (if changing)
        update_data = data.model_dump(exclude_unset=True)

        if "phone" in update_data and update_data["phone"] != patient.phone:
            existing = await self.repository.get_by_phone(update_data["phone"])
            if existing and existing.id != id:
                raise ValueError(f"Phone {update_data['phone']} already in use")

        if "email" in update_data and update_data["email"] != patient.email:
            if update_data["email"]:
                existing = await self.repository.get_by_email(update_data["email"])
                if existing and existing.id != id:
                    raise ValueError(f"Email {update_data['email']} already in use")

        # Apply updates
        for field, value in update_data.items():
            setattr(patient, field, value)

        # Update full_name if needed
        if "first_name" in update_data or "last_name" in update_data:
            patient.full_name = f"{patient.first_name} {patient.last_name}"

        # Save
        patient = await self.repository.update(patient)

        # Invalidate cache
        await self._invalidate_patient_cache(id, patient.phone)

        # Emit event
        await event_bus.emit(
            Event(
                event_type="patient.updated",
                data={
                    "patient_id": patient.id,
                    "updated_fields": list(update_data.keys()),
                    "updated_by": updated_by,
                },
            )
        )

        logger.info(
            f"Updated patient {id}",
            extra={
                "patient_id": id,
                "updated_fields": list(update_data.keys()),
                "updated_by": updated_by,
            },
        )

        return patient

    async def delete_patient(
        self,
        id: int,
        deleted_by: Optional[str] = None,
        hard_delete: bool = False,
    ) -> bool:
        """
        Delete patient (soft or hard)

        Args:
            id: Patient ID
            deleted_by: User who deleted
            hard_delete: Whether to hard delete (default: soft)

        Returns:
            True if deleted
        """
        if hard_delete:
            # Check feature flag for hard delete permission
            if not await is_feature_enabled("patient_hard_delete"):
                logger.warning(
                    "Hard delete attempted but feature flag disabled",
                    extra={"patient_id": id},
                )
                hard_delete = False

        if hard_delete:
            result = await self.repository.delete(id)
        else:
            result = await self.repository.soft_delete(id)

        if result:
            # Invalidate cache
            await self._invalidate_patient_cache(id)

            # Emit event
            await event_bus.emit(
                Event(
                    event_type="patient.deleted",
                    data={
                        "patient_id": id,
                        "hard_delete": hard_delete,
                        "deleted_by": deleted_by,
                    },
                )
            )

            logger.info(
                f"Deleted patient {id}",
                extra={
                    "patient_id": id,
                    "hard_delete": hard_delete,
                    "deleted_by": deleted_by,
                },
            )

        return result

    async def get_ai_profile(self, id: int) -> Optional[dict]:
        """
        Get AI-optimized patient profile for Mortarium

        Args:
            id: Patient ID

        Returns:
            AI profile dictionary
        """
        # Check feature flag
        if not await is_feature_enabled("ai_patient_profiles"):
            logger.debug("AI patient profiles feature flag disabled")
            return None

        cache_key = f"patient:ai_profile:{id}"

        # Try cache
        cached = await cache_service.get(cache_key)
        if cached:
            CACHE_HITS_TOTAL.labels(cache_type="ai_profile").inc()
            return cached

        CACHE_MISSES_TOTAL.labels(cache_type="ai_profile").inc()

        # Get from repository
        profile = await self.repository.get_ai_profile(id)

        # Cache
        if profile:
            await cache_service.set(cache_key, profile, ttl=self.cache_ttl)

        return profile

    async def get_statistics(self) -> dict:
        """
        Get patient statistics

        Returns:
            Statistics dictionary
        """
        total = await self.repository.count()
        active = await self.repository.count(is_active=True)

        loyalty_stats = await self.repository.get_loyalty_tiers_stats()
        country_stats = await self.repository.get_country_stats()

        return {
            "total": total,
            "active": active,
            "inactive": total - active,
            "by_loyalty_tier": loyalty_stats,
            "by_country": country_stats,
        }

    async def record_visit(
        self,
        id: int,
        purchase_amount: int = 0,
    ) -> Optional[Patient]:
        """
        Record patient visit

        Args:
            id: Patient ID
            purchase_amount: Purchase amount

        Returns:
            Updated patient
        """
        patient = await self.repository.record_visit(id, purchase_amount)

        if patient:
            # Invalidate cache
            await self._invalidate_patient_cache(id, patient.phone)

            # Emit event
            await event_bus.emit(
                Event(
                    event_type="patient.visit_recorded",
                    data={
                        "patient_id": id,
                        "purchase_amount": purchase_amount,
                    },
                )
            )

        return patient

    async def _invalidate_patient_cache(
        self,
        patient_id: int,
        phone: Optional[str] = None,
    ) -> None:
        """Invalidate all cache entries for patient"""
        await cache_service.delete(f"patient:{patient_id}")
        await cache_service.delete(f"patient:ai_profile:{patient_id}")

        if phone:
            await cache_service.delete(f"patient:phone:{phone}")

        logger.debug(f"Invalidated cache for patient {patient_id}")
