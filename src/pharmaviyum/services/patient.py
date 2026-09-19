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
        self, data: PatientCreate, created_by: Optional[str] = None
    ) -> Patient:
        existing = await self.repository.get_by_phone(data.phone)
        if existing:
            raise ValueError(f"Patient with phone {data.phone} already exists")
        if data.email:
            existing = await self.repository.get_by_email(data.email)
            if existing:
                raise ValueError(f"Patient with email {data.email} already exists")

        patient = Patient(
            **data.model_dump(), full_name=f"{data.first_name} {data.last_name}"
        )
        patient = await self.repository.create(patient)
        PATIENTS_CREATED_TOTAL.labels(country=patient.country).inc()
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
            "Created patient %s",
            patient.id,
            extra={"patient_id": patient.id, "created_by": created_by},
        )
        return patient

    async def get_patient(self, id: int, use_cache: bool = True) -> Optional[Patient]:
        cache_key = f"patient:{id}"
        if use_cache:
            cached = await cache_service.get(cache_key)
            if cached:
                CACHE_HITS_TOTAL.labels(cache_type="patient").inc()
                return cached
        CACHE_MISSES_TOTAL.labels(cache_type="patient").inc()
        patient = await self.repository.get_by_id_with_relations(id)
        if patient and use_cache:
            await cache_service.set(cache_key, patient, ttl=self.cache_ttl)
        return patient

    async def get_patient_by_phone(self, phone: str) -> Optional[Patient]:
        cache_key = f"patient:phone:{phone}"
        cached = await cache_service.get(cache_key)
        if cached:
            CACHE_HITS_TOTAL.labels(cache_type="patient_phone").inc()
            return cached
        CACHE_MISSES_TOTAL.labels(cache_type="patient_phone").inc()
        patient = await self.repository.get_by_phone(phone)
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
        patient = await self.get_patient(id, use_cache=False)
        if not patient:
            return None
        update_data = data.model_dump(exclude_unset=True)
        if "phone" in update_data and update_data["phone"] != patient.phone:
            existing = await self.repository.get_by_phone(update_data["phone"])
            if existing and existing.id != id:
                raise ValueError(f"Phone {update_data['phone']} already in use")
        if (
            "email" in update_data
            and update_data["email"] != patient.email
            and update_data["email"]
        ):
            existing = await self.repository.get_by_email(update_data["email"])
            if existing and existing.id != id:
                raise ValueError(f"Email {update_data['email']} already in use")
        for field, value in update_data.items():
            setattr(patient, field, value)
        if "first_name" in update_data or "last_name" in update_data:
            patient.full_name = f"{patient.first_name} {patient.last_name}"
        patient = await self.repository.update(patient)
        await self._invalidate_patient_cache(id, patient.phone)
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
        return patient

    async def delete_patient(
        self,
        id: int,
        deleted_by: Optional[str] = None,
        hard_delete: bool = False,
    ) -> bool:
        if hard_delete and not await is_feature_enabled("patient_hard_delete"):
            hard_delete = False
        result = (
            await self.repository.delete(id)
            if hard_delete
            else await self.repository.soft_delete(id)
        )
        if result:
            await self._invalidate_patient_cache(id)
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
        return result

    async def get_ai_profile(self, id: int) -> Optional[dict]:
        if not await is_feature_enabled("ai_patient_profiles"):
            return None
        cache_key = f"patient:ai_profile:{id}"
        cached = await cache_service.get(cache_key)
        if cached:
            CACHE_HITS_TOTAL.labels(cache_type="ai_profile").inc()
            return cached
        CACHE_MISSES_TOTAL.labels(cache_type="ai_profile").inc()
        profile = await self.repository.get_ai_profile(id)
        if profile:
            await cache_service.set(cache_key, profile, ttl=self.cache_ttl)
        return profile

    async def get_statistics(self) -> dict:
        total = await self.repository.count()
        active = await self.repository.count(is_active=True)
        return {
            "total": total,
            "active": active,
            "inactive": total - active,
            "total_purchase_value": await self.repository.get_total_purchase_value(),
            "total_loyalty_points": await self.repository.get_total_loyalty_points(),
            "by_loyalty_tier": await self.repository.get_loyalty_tiers_stats(),
            "by_country": await self.repository.get_country_stats(),
        }

    async def record_visit(self, id: int) -> Optional[Patient]:
        patient = await self.repository.record_visit(id)
        if patient:
            await self._invalidate_patient_cache(id, patient.phone)
            await event_bus.emit(
                Event(
                    event_type="patient.visit_recorded",
                    data={"patient_id": id},
                )
            )
        return patient

    async def _invalidate_patient_cache(
        self, patient_id: int, phone: Optional[str] = None
    ) -> None:
        await cache_service.delete(f"patient:{patient_id}")
        await cache_service.delete(f"patient:ai_profile:{patient_id}")
        if phone:
            await cache_service.delete(f"patient:phone:{phone}")
