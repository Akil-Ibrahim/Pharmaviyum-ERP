"""Patient application service.

Business workflows depend on application ports; infrastructure repositories
remain replaceable details.
"""

from typing import Optional

from src.pharmaviyum.application.ports.repositories import PatientRepositoryPort
from src.pharmaviyum.core.feature_flags import is_feature_enabled
from src.pharmaviyum.core.logging import get_logger
from src.pharmaviyum.core.metrics import (
    CACHE_HITS_TOTAL,
    CACHE_MISSES_TOTAL,
    PATIENTS_CREATED_TOTAL,
)
from src.pharmaviyum.models.patients import Patient
from src.pharmaviyum.schemas.patient import PatientCreate, PatientUpdate
from src.pharmaviyum.services.cache import cache_service
from src.pharmaviyum.services.event_bus import Event, event_bus

logger = get_logger(__name__)


class PatientService:
    """Application service for patient use cases."""

    def __init__(self, repository: PatientRepositoryPort):
        self.repository = repository
        self.cache_ttl = 3600

    async def create_patient(
        self,
        data: PatientCreate,
        created_by: Optional[str] = None,
        pharmacy_id: int | None = None,
    ) -> Patient:
        existing = await self.repository.get_by_phone(
            data.phone, pharmacy_id=pharmacy_id
        )
        if existing:
            raise ValueError(f"Patient with phone {data.phone} already exists")
        if data.email:
            existing = await self.repository.get_by_email(
                data.email, pharmacy_id=pharmacy_id
            )
            if existing:
                raise ValueError(f"Patient with email {data.email} already exists")

        payload = data.model_dump()
        if pharmacy_id is not None:
            payload["pharmacy_id"] = pharmacy_id
        patient = Patient(**payload, full_name=f"{data.first_name} {data.last_name}")
        patient = await self.repository.create(patient)
        reloaded_patient = await self.repository.get_by_id_with_relations(
            patient.id, pharmacy_id=pharmacy_id
        )
        if reloaded_patient is None:
            raise RuntimeError("Created patient could not be reloaded")
        PATIENTS_CREATED_TOTAL.labels(country=reloaded_patient.country).inc()
        await event_bus.emit(
            Event(
                event_type="patient.created",
                data={
                    "patient_id": reloaded_patient.id,
                    "full_name": reloaded_patient.full_name,
                    "phone": reloaded_patient.phone,
                    "country": reloaded_patient.country,
                    "created_by": created_by,
                },
            )
        )
        logger.info(
            "Created patient %s",
            reloaded_patient.id,
            extra={"patient_id": reloaded_patient.id, "created_by": created_by},
        )
        return reloaded_patient

    async def get_patient(
        self, id: int, use_cache: bool = True, pharmacy_id: int | None = None
    ) -> Optional[Patient]:
        cache_key = f"patient:{pharmacy_id or 0}:{id}"
        if use_cache:
            cached = await cache_service.get(cache_key)
            if cached:
                CACHE_HITS_TOTAL.labels(cache_type="patient").inc()
                return cached
        CACHE_MISSES_TOTAL.labels(cache_type="patient").inc()
        patient = await self.repository.get_by_id_with_relations(
            id, pharmacy_id=pharmacy_id
        )
        if patient and use_cache:
            await cache_service.set(cache_key, patient, ttl=self.cache_ttl)
        return patient

    async def get_patient_by_phone(
        self, phone: str, pharmacy_id: int | None = None
    ) -> Optional[Patient]:
        cache_key = f"patient:phone:{pharmacy_id or 0}:{phone}"
        cached = await cache_service.get(cache_key)
        if cached:
            CACHE_HITS_TOTAL.labels(cache_type="patient_phone").inc()
            return cached
        CACHE_MISSES_TOTAL.labels(cache_type="patient_phone").inc()
        patient = await self.repository.get_by_phone(phone, pharmacy_id=pharmacy_id)
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
        pharmacy_id: int | None = None,
    ) -> tuple[list[Patient], int]:
        skip = (page - 1) * page_size
        return await self.repository.search(
            query_text=query_text,
            city=city,
            country=country,
            loyalty_tier=loyalty_tier,
            is_active=is_active,
            skip=skip,
            limit=page_size,
            pharmacy_id=pharmacy_id,
        )
