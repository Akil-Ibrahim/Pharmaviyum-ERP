"""
AI tasks for Mortarium AI integration
Best practice 2026: Async AI processing with GPU queue management
"""

from typing import Optional

from src.pharmaviyum.core.logging import get_logger
from src.pharmaviyum.workers.base import BaseTask, RetryConfig
from src.pharmaviyum.workers.queues import TaskQueue

logger = get_logger(__name__)


class ReviewPrescriptionTask(BaseTask):
    """AI review of prescription for safety checks"""

    name = "review_prescription"
    queue = TaskQueue.AI_TASKS.value
    timeout_seconds = 120
    retry_config = RetryConfig(max_attempts=2, base_delay_seconds=5.0)

    async def execute(
        self,
        prescription_id: int,
    ) -> dict:
        """
        Review prescription with Mortarium AI

        Args:
            prescription_id: Prescription ID

        Returns:
            Review result with AI score and warnings
        """
        logger.info(f"Reviewing prescription {prescription_id}")

        # Fetch prescription with patient and items
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        from src.pharmaviyum.core.database import async_session
        from src.pharmaviyum.models.prescriptions import Prescription

        async with async_session() as session:
            result = await session.execute(
                select(Prescription)
                .options(
                    selectinload(Prescription.items),
                    selectinload(Prescription.patient).selectinload("allergies"),
                    selectinload(Prescription.patient).selectinload("conditions"),
                )
                .where(Prescription.id == prescription_id)
            )
            prescription = result.scalar_one_or_none()

            if not prescription:
                raise ValueError(f"Prescription {prescription_id} not found")

            # Prepare context for AI
            context = self._build_ai_context(prescription)

            # Call Mortarium AI
            # TODO: Implement actual AI call
            ai_result = await self._call_mortarium_ai(
                task="prescription_review",
                context=context,
            )

            # Update prescription with AI review
            prescription.ai_reviewed = True
            prescription.ai_review_score = ai_result.get("score", 0)
            prescription.ai_warnings = str(ai_result.get("warnings", []))

            await session.commit()

        return {
            "prescription_id": prescription_id,
            "score": ai_result.get("score"),
            "warnings": ai_result.get("warnings", []),
            "recommendations": ai_result.get("recommendations", []),
        }

    def _build_ai_context(self, prescription) -> dict:
        """Build context for AI review"""
        patient = prescription.patient

        return {
            "patient": {
                "id": patient.id,
                "age": self._calculate_age(patient.date_of_birth),
                "gender": patient.gender,
                "allergies": [a.allergen_name for a in patient.allergies],
                "conditions": [c.condition_name for c in patient.conditions],
            },
            "prescription": {
                "type": prescription.prescription_type,
                "items": [
                    {
                        "name": item.medication_name,
                        "dosage": item.dosage,
                        "frequency": item.frequency,
                        "duration": item.duration,
                    }
                    for item in prescription.items
                ],
            },
        }

    def _calculate_age(self, dob) -> Optional[int]:
        """Calculate age from date of birth"""
        if not dob:
            return None

        from datetime import date

        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    async def _call_mortarium_ai(
        self,
        task: str,
        context: dict,
    ) -> dict:
        """
        Call Mortarium AI service

        Args:
            task: Task type
            context: AI context

        Returns:
            AI result
        """
        # TODO: Implement actual Mortarium AI client
        # from src.pharmaviyum.mortarium.client import MortariumClient
        # client = MortariumClient()
        # return await client.process(task, context)

        # Mock response for now
        return {
            "score": 85,
            "warnings": [],
            "recommendations": [],
        }


class CheckDrugInteractionTask(BaseTask):
    """Check drug interactions using Mortarium AI"""

    name = "check_drug_interaction"
    queue = TaskQueue.AI_TASKS.value
    timeout_seconds = 60
    retry_config = RetryConfig(max_attempts=2)

    async def execute(
        self,
        drug_names: list[str],
        patient_id: Optional[int] = None,
    ) -> dict:
        """
        Check drug interactions

        Args:
            drug_names: List of drug names to check
            patient_id: Optional patient ID for context

        Returns:
            Interaction check result
        """
        logger.info(
            "Checking drug interactions",
            extra={"drugs": drug_names, "patient_id": patient_id},
        )

        # Build context
        context = {"drugs": drug_names}

        if patient_id:
            # Fetch patient allergies and conditions
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload

            from src.pharmaviyum.core.database import async_session
            from src.pharmaviyum.models.patients import Patient

            async with async_session() as session:
                result = await session.execute(
                    select(Patient)
                    .options(
                        selectinload(Patient.allergies),
                        selectinload(Patient.conditions),
                    )
                    .where(Patient.id == patient_id)
                )
                patient = result.scalar_one_or_none()

                if patient:
                    context["patient"] = {
                        "allergies": [a.allergen_name for a in patient.allergies],
                        "conditions": [c.condition_name for c in patient.conditions],
                    }

        # Call AI
        ai_result = await self._call_mortarium_ai(
            task="drug_interaction",
            context=context,
        )

        return ai_result

    async def _call_mortarium_ai(self, task: str, context: dict) -> dict:
        """Call Mortarium AI"""
        # TODO: Implement actual AI call
        return {
            "interactions": [],
            "severity": "none",
            "recommendations": [],
        }


class GenerateRecommendationTask(BaseTask):
    """Generate personalized recommendations using Mortarium AI"""

    name = "generate_recommendation"
    queue = TaskQueue.AI_TASKS.value
    timeout_seconds = 60
    retry_config = RetryConfig(max_attempts=2)

    async def execute(
        self,
        patient_id: int,
        symptom: Optional[str] = None,
        query_type: str = "otc",  # otc/upsell/personalized
    ) -> dict:
        """
        Generate AI recommendation

        Args:
            patient_id: Patient ID
            symptom: Symptom description (for OTC)
            query_type: Type of recommendation

        Returns:
            Recommendation result
        """
        logger.info(
            "Generating recommendation",
            extra={
                "patient_id": patient_id,
                "symptom": symptom,
                "query_type": query_type,
            },
        )

        # Fetch patient profile
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        from src.pharmaviyum.core.database import async_session
        from src.pharmaviyum.models.patients import Patient

        async with async_session() as session:
            result = await session.execute(
                select(Patient)
                .options(
                    selectinload(Patient.allergies),
                    selectinload(Patient.conditions),
                )
                .where(Patient.id == patient_id)
            )
            patient = result.scalar_one_or_none()

            if not patient:
                raise ValueError(f"Patient {patient_id} not found")

            # Build context
            context = {
                "patient": {
                    "id": patient.id,
                    "age": self._calculate_age(patient.date_of_birth),
                    "gender": patient.gender,
                    "allergies": [a.allergen_name for a in patient.allergies],
                    "conditions": [c.condition_name for c in patient.conditions],
                    "loyalty_tier": patient.loyalty_tier,
                },
                "symptom": symptom,
                "query_type": query_type,
            }

            # Call AI
            ai_result = await self._call_mortarium_ai(
                task="recommendation",
                context=context,
            )

        return ai_result

    def _calculate_age(self, dob) -> Optional[int]:
        """Calculate age from date of birth"""
        if not dob:
            return None
        from datetime import date

        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    async def _call_mortarium_ai(self, task: str, context: dict) -> dict:
        """Call Mortarium AI"""
        # TODO: Implement actual AI call
        return {
            "recommendation": None,
            "confidence": 0.0,
            "reasoning": [],
        }
