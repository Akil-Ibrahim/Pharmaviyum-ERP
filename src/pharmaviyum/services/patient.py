"""Patient application service.

This service is the application orchestration boundary. Persistence is
expressed through the application repository port so the business workflow
is independent of SQLAlchemy repository implementations.
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
    ) -> Patient:
        """Create a patient while enforcing application-level invariants."""
        existing = await self.repository.get_by_phone(data.phone)
        if existing:
            raise ValueError(f"Patient with phone {data.phone} already exists")

        if data.email:
            existing = await self.repository.get_by_email(data.email)
            if existing:
                raise ValueError(f"Patient with email {data.email} already exists")

        patient = Patient(
            **data.model_dump(),
            full_name=f"{data.first_name} {data.last_name}",
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
        return patient
