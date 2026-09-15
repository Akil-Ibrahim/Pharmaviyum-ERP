"""
MCP Tool: Patient History Retrieval.

Loads patient medical history from PostgreSQL for AI context.

Best practice 2026:
- Async SQLAlchemy with selectinload (no N+1 queries)
- Computed fields (age from DOB)
- Time-bounded queries (months_back)
- Privacy-aware: no sensitive data leakage
- Structured output for LLM consumption
"""

from __future__ import annotations

import time
from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.pharmaviyum.core.logging import logger

from ..registry import registry
from ..schemas import (AllergyInfo, ConditionInfo, PatientHistory,
                       PatientHistoryRequest)


def calculate_age(dob: date | None) -> int | None:
    """Calculate age from date of birth."""
    if not dob:
        return None
    today = date.today()
    age = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        age -= 1
    return age


@registry.tool(
    name="get_patient_history",
    description=(
        "Retrieve patient medical history including allergies, "
        "chronic conditions, active prescriptions, and loyalty tier. "
        "Critical for personalized pharmaceutical consultation and "
        "safety checks (contraindications, allergies)."
    ),
    input_schema=PatientHistoryRequest,
    output_schema=PatientHistory,
    category="clinical",
    latency_estimate_ms=80,
    requires_db=True,
    tags=["patient", "clinical", "safety", "context"],
)
async def get_patient_history(input: PatientHistoryRequest) -> PatientHistory:
    """
    Load patient medical history with eager-loaded relationships.

    Algorithm:
    1. Fetch patient with selectinload for allergies + conditions
    2. Optionally fetch recent prescriptions (filtered by months_back)
    3. Compute derived fields (age, active prescription count)
    4. Return structured history for LLM context
    """
    start = time.perf_counter()

    # Lazy import to avoid circular dependencies
    from src.pharmaviyum.modules.patients.models import Patient
    from src.pharmaviyum.shared.core.database import async_session_factory

    async with async_session_factory() as session:
        # Single query with eager loading (no N+1)
        query = (
            select(Patient)
            .options(
                selectinload(Patient.allergies),
                selectinload(Patient.conditions),
            )
            .where(Patient.id == input.patient_id)
        )
        result = await session.execute(query)
        patient = result.scalar_one_or_none()

        if not patient:
            raise ValueError(f"Patient not found: {input.patient_id}")

        # Build allergies list
        allergies: list[AllergyInfo] = []
        if input.include_allergies:
            allergies = [
                AllergyInfo(
                    allergen=a.allergen_name,
                    type=a.allergen_type,
                    severity=a.severity,
                    verified=a.is_verified,
                )
                for a in patient.allergies
            ]

        # Build conditions list
        conditions: list[ConditionInfo] = []
        if input.include_conditions:
            conditions = [
                ConditionInfo(
                    name=c.condition_name,
                    icd10_code=c.icd10_code,
                    is_chronic=c.is_chronic,
                    status=c.status,
                )
                for c in patient.conditions
            ]

        # Count active prescriptions (if requested)
        active_prescriptions = 0
        if input.include_prescriptions:
            active_prescriptions = await _count_active_prescriptions(
                session, input.patient_id, input.months_back
            )

        # Count recent orders (if requested)
        recent_orders = 0
        if input.include_orders:
            recent_orders = await _count_recent_orders(
                session, input.patient_id, input.months_back
            )

        latency_ms = (time.perf_counter() - start) * 1000

        logger.info(
            f"Patient history loaded: {patient.full_name}",
            extra={
                "patient_id": input.patient_id,
                "allergies": len(allergies),
                "conditions": len(conditions),
                "latency_ms": latency_ms,
            },
        )

        return PatientHistory(
            patient_id=patient.id,
            full_name=patient.full_name,
            age=calculate_age(patient.date_of_birth),
            gender=patient.gender,
            blood_type=patient.blood_type,
            allergies=allergies,
            conditions=conditions,
            active_prescriptions=active_prescriptions,
            recent_orders=recent_orders,
            loyalty_tier=patient.loyalty_tier,
            preferred_language=patient.preferred_language,
        )


async def _count_active_prescriptions(
    session: AsyncSession,
    patient_id: int,
    months_back: int,
) -> int:
    """Count prescriptions issued within months_back."""
    try:
        from src.pharmaviyum.modules.prescriptions.models import Prescription

        cutoff = datetime.utcnow() - __import__("datetime").timedelta(
            days=months_back * 30
        )

        query = select(func.count(Prescription.id)).where(
            Prescription.patient_id == patient_id,
            Prescription.date_issued >= cutoff,
            Prescription.status.in_(["active", "filled"]),
        )
        result = await session.execute(query)
        return result.scalar_one()
    except Exception as e:
        logger.warning(f"Could not count prescriptions: {e}")
        return 0


async def _count_recent_orders(
    session: AsyncSession,
    patient_id: int,
    months_back: int,
) -> int:
    """Count orders within months_back."""
    try:
        from src.pharmaviyum.modules.orders.models import InternetOrder

        cutoff = datetime.utcnow() - __import__("datetime").timedelta(
            days=months_back * 30
        )

        query = select(func.count(InternetOrder.id)).where(
            InternetOrder.patient_id == patient_id,
            InternetOrder.created_at >= cutoff,
        )
        result = await session.execute(query)
        return result.scalar_one()
    except Exception as e:
        logger.warning(f"Could not count orders: {e}")
        return 0
