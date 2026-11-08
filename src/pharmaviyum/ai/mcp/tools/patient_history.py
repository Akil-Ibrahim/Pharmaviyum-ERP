"""
MCP Tool: Patient History Retrieval.

Loads patient medical history from PostgreSQL for AI context.

Tenant authorization is enforced from trusted MCP context, never tool input.
"""

from __future__ import annotations

import time
from datetime import date, datetime, timedelta
from typing import Literal, cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.pharmaviyum.core.logging import logger
from src.pharmaviyum.models.patients import Patient

from ..context import require_mcp_context
from ..registry import registry
from ..schemas import AllergyInfo, ConditionInfo, PatientHistory, PatientHistoryRequest


def calculate_age(dob: date | None) -> int | None:
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
        "Retrieve patient medical history including allergies, chronic "
        "conditions, active prescriptions, and loyalty tier. "
        "Critical for personalized pharmaceutical consultation and safety checks."
    ),
    input_schema=PatientHistoryRequest,
    output_schema=PatientHistory,
    category="clinical",
    latency_estimate_ms=80,
    requires_db=True,
    tags=["patient", "clinical", "safety", "context"],
)
async def get_patient_history(input: PatientHistoryRequest) -> PatientHistory:
    """Load patient history only inside the authenticated pharmacy tenant."""
    start = time.perf_counter()
    auth_context = require_mcp_context()

    from src.pharmaviyum.shared.core.database import async_session_factory

    async with async_session_factory() as session:
        query = (
            select(Patient)
            .options(selectinload(Patient.allergies), selectinload(Patient.conditions))
            .where(
                Patient.id == input.patient_id,
                Patient.pharmacy_id == auth_context.pharmacy_id,
                Patient.is_active.is_(True),
            )
        )
        result = await session.execute(query)
        patient = result.scalar_one_or_none()
        if not patient:
            raise ValueError("Patient not found or not accessible")

        allergies = (
            [
                AllergyInfo(
                    allergen=a.allergen_name,
                    type=cast(
                        Literal["drug", "food", "environmental"], a.allergen_type
                    ),
                    severity=cast(Literal["mild", "moderate", "severe"], a.severity),
                    verified=a.is_verified,
                )
                for a in patient.allergies
            ]
            if input.include_allergies
            else []
        )
        conditions = (
            [
                ConditionInfo(
                    name=c.condition_name,
                    icd10_code=c.icd10_code,
                    is_chronic=c.is_chronic,
                    status=cast(Literal["active", "resolved", "managed"], c.status),
                )
                for c in patient.conditions
            ]
            if input.include_conditions
            else []
        )

        active_prescriptions = (
            await _count_active_prescriptions(
                session, input.patient_id, input.months_back, auth_context.pharmacy_id
            )
            if input.include_prescriptions
            else 0
        )
        recent_orders = (
            await _count_recent_orders(
                session, input.patient_id, input.months_back, auth_context.pharmacy_id
            )
            if input.include_orders
            else 0
        )

        logger.info(
            "Patient history loaded",
            extra={
                "allergy_count": len(allergies),
                "condition_count": len(conditions),
                "latency_ms": (time.perf_counter() - start) * 1000,
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
    session: AsyncSession, patient_id: int, months_back: int, pharmacy_id: int
) -> int:
    """Count prescriptions within the authenticated pharmacy tenant."""
    try:
        from src.pharmaviyum.models.prescription import Prescription

        cutoff = datetime.utcnow() - timedelta(days=months_back * 30)
        query = (
            select(func.count(Prescription.id))
            .join(Patient, Prescription.patient_id == Patient.id)
            .where(
                Prescription.patient_id == patient_id,
                Patient.pharmacy_id == pharmacy_id,
                Prescription.issued_at >= cutoff,
                Prescription.status.in_(["active", "filled"]),
            )
        )
        result = await session.execute(query)
        return result.scalar_one()
    except Exception as exc:
        logger.warning(
            "Could not count prescriptions",
            extra={"error_type": type(exc).__name__},
        )
        return 0


async def _count_recent_orders(
    session: AsyncSession, patient_id: int, months_back: int, pharmacy_id: int
) -> int:
    """Count orders within the authenticated pharmacy tenant."""
    try:
        from src.pharmaviyum.models.order import Order

        cutoff = datetime.utcnow() - timedelta(days=months_back * 30)
        query = (
            select(func.count(Order.id))
            .join(Patient, Order.patient_id == Patient.id)
            .where(
                Order.patient_id == patient_id,
                Patient.pharmacy_id == pharmacy_id,
                Order.created_at >= cutoff,
            )
        )
        result = await session.execute(query)
        return result.scalar_one()
    except Exception as exc:
        logger.warning("Could not count orders: %s", exc)
        return 0
