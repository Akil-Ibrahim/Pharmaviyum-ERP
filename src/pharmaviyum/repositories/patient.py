"""
Patient repository - Data access layer for patients
Best practice 2026: Repository pattern with advanced queries
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.pharmaviyum.core.logging import get_logger
from src.pharmaviyum.core.repository import BaseRepository
from src.pharmaviyum.models.patients import (Patient, PatientAllergy,
                                             PatientCondition)

logger = get_logger(__name__)


class PatientRepository(BaseRepository[Patient]):
    """
    Patient repository with advanced query methods

    Extends BaseRepository with patient-specific operations:
    - Search with multiple filters
    - Eager loading of relationships
    - Soft delete support
    - Statistics queries
    - Bulk operations
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with Patient model"""
        super().__init__(Patient, session)

    async def get_by_id_with_relations(
        self,
        id: int,
        include_allergies: bool = True,
        include_conditions: bool = True,
        include_insurances: bool = True,
        include_consultations: bool = False,
    ) -> Optional[Patient]:
        """
        Get patient by ID with eager-loaded relationships

        Args:
            id: Patient ID
            include_allergies: Load allergies
            include_conditions: Load conditions
            include_insurances: Load insurances
            include_consultations: Load consultations

        Returns:
            Patient with relationships or None
        """
        query = select(Patient).where(Patient.id == id)

        if include_allergies:
            query = query.options(selectinload(Patient.allergies))
        if include_conditions:
            query = query.options(selectinload(Patient.conditions))
        if include_insurances:
            query = query.options(selectinload(Patient.insurances))
        if include_consultations:
            query = query.options(selectinload(Patient.consultations))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> Optional[Patient]:
        """
        Get patient by phone number

        Args:
            phone: Phone number

        Returns:
            Patient or None
        """
        result = await self.session.execute(
            select(Patient).where(Patient.phone == phone)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[Patient]:
        """
        Get patient by email

        Args:
            email: Email address

        Returns:
            Patient or None
        """
        result = await self.session.execute(
            select(Patient).where(Patient.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_external_id(
        self,
        external_id: str,
        pos_system: str,
    ) -> Optional[Patient]:
        """
        Get patient by external ID from POS system

        Args:
            external_id: External ID from POS
            pos_system: POS system name

        Returns:
            Patient or None
        """
        result = await self.session.execute(
            select(Patient).where(
                Patient.external_id == external_id,
                Patient.pos_system == pos_system,
            )
        )
        return result.scalar_one_or_none()

    async def search(
        self,
        query_text: Optional[str] = None,
        city: Optional[str] = None,
        country: Optional[str] = None,
        loyalty_tier: Optional[str] = None,
        is_active: Optional[bool] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Patient], int]:
        """
        Advanced patient search with multiple filters

        Args:
            query_text: Search by name or phone
            city: Filter by city
            country: Filter by country
            loyalty_tier: Filter by loyalty tier
            is_active: Filter by active status
            date_from: Filter by created_at (from)
            date_to: Filter by created_at (to)
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            Tuple of (patients list, total count)
        """
        # Build query
        query = select(Patient)
        count_query = select(func.count(Patient.id))

        # Apply filters
        conditions = []

        if query_text:
            search_pattern = f"%{query_text}%"
            conditions.append(
                or_(
                    Patient.full_name.ilike(search_pattern),
                    Patient.phone.ilike(search_pattern),
                    Patient.email.ilike(search_pattern),
                )
            )

        if city:
            conditions.append(Patient.city == city)

        if country:
            conditions.append(Patient.country == country)

        if loyalty_tier:
            conditions.append(Patient.loyalty_tier == loyalty_tier)

        if is_active is not None:
            conditions.append(Patient.is_active == is_active)

        if date_from:
            conditions.append(Patient.created_at >= date_from)

        if date_to:
            conditions.append(Patient.created_at <= date_to)

        # Apply conditions
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Get total count
        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        # Apply pagination and ordering
        query = query.offset(skip).limit(limit).order_by(Patient.updated_at.desc())

        # Execute query
        result = await self.session.execute(query)
        patients = list(result.scalars().all())

        return patients, total

    async def get_loyalty_tiers_stats(self) -> dict:
        """
        Get statistics by loyalty tier

        Returns:
            Dictionary with tier counts
        """
        result = await self.session.execute(
            select(
                Patient.loyalty_tier,
                func.count(Patient.id),
            )
            .where(Patient.is_active)
            .group_by(Patient.loyalty_tier)
        )

        return {tier: count for tier, count in result.all()}

    async def get_country_stats(self) -> dict:
        """
        Get statistics by country

        Returns:
            Dictionary with country counts
        """
        result = await self.session.execute(
            select(
                Patient.country,
                func.count(Patient.id),
            )
            .where(Patient.is_active)
            .group_by(Patient.country)
        )

        return {country: count for country, count in result.all()}

    async def get_recent_patients(self, limit: int = 10) -> list[Patient]:
        """
        Get recently created patients

        Args:
            limit: Number of patients to return

        Returns:
            List of recent patients
        """
        result = await self.session.execute(
            select(Patient)
            .where(Patient.is_active)
            .order_by(Patient.created_at.desc())
            .limit(limit)
        )

        return list(result.scalars().all())

    async def get_top_customers(self, limit: int = 10) -> list[Patient]:
        """
        Get top customers by total purchases

        Args:
            limit: Number of patients to return

        Returns:
            List of top customers
        """
        result = await self.session.execute(
            select(Patient)
            .where(Patient.is_active)
            .order_by(Patient.total_purchases.desc())
            .limit(limit)
        )

        return list(result.scalars().all())

    async def soft_delete(self, id: int) -> bool:
        """
        Soft delete patient (set is_active=False)

        Args:
            id: Patient ID

        Returns:
            True if deleted
        """
        patient = await self.get_by_id(id)
        if not patient:
            return False

        patient.is_active = False
        await self.session.flush()

        logger.info(f"Soft deleted patient {id}")
        return True

    async def restore(self, id: int) -> bool:
        """
        Restore soft-deleted patient

        Args:
            id: Patient ID

        Returns:
            True if restored
        """
        patient = await self.get_by_id(id)
        if not patient:
            return False

        patient.is_active = True
        await self.session.flush()

        logger.info(f"Restored patient {id}")
        return True

    async def update_loyalty(
        self,
        id: int,
        tier: str,
        points: Optional[int] = None,
    ) -> Optional[Patient]:
        """
        Update patient loyalty information

        Args:
            id: Patient ID
            tier: New loyalty tier
            points: New points (optional)

        Returns:
            Updated patient
        """
        patient = await self.get_by_id(id)
        if not patient:
            return None

        patient.loyalty_tier = tier
        if points is not None:
            patient.loyalty_points = points

        await self.session.flush()
        await self.session.refresh(patient)

        return patient

    async def record_visit(
        self, id: int, purchase_amount: int = 0
    ) -> Optional[Patient]:
        """
        Record patient visit and update statistics

        Args:
            id: Patient ID
            purchase_amount: Purchase amount in smallest currency unit

        Returns:
            Updated patient
        """
        patient = await self.get_by_id(id)
        if not patient:
            return None

        patient.visit_count += 1
        patient.total_purchases += purchase_amount
        patient.last_visit_date = datetime.utcnow()

        await self.session.flush()
        await self.session.refresh(patient)

        return patient

    async def add_allergy(
        self,
        patient_id: int,
        allergen_name: str,
        allergen_type: str = "drug",
        severity: str = "moderate",
        reaction: Optional[str] = None,
    ) -> PatientAllergy:
        """
        Add allergy to patient

        Args:
            patient_id: Patient ID
            allergen_name: Allergen name
            allergen_type: Type (drug/food/environmental/other)
            severity: Severity level
            reaction: Reaction description

        Returns:
            Created allergy
        """
        allergy = PatientAllergy(
            patient_id=patient_id,
            allergen_name=allergen_name,
            allergen_type=allergen_type,
            severity=severity,
            reaction=reaction,
        )

        self.session.add(allergy)
        await self.session.flush()
        await self.session.refresh(allergy)

        return allergy

    async def add_condition(
        self,
        patient_id: int,
        condition_name: str,
        icd10_code: Optional[str] = None,
        is_chronic: bool = False,
    ) -> PatientCondition:
        """
        Add condition to patient

        Args:
            patient_id: Patient ID
            condition_name: Condition name
            icd10_code: ICD-10 code
            is_chronic: Whether condition is chronic

        Returns:
            Created condition
        """
        condition = PatientCondition(
            patient_id=patient_id,
            condition_name=condition_name,
            icd10_code=icd10_code,
            is_chronic=is_chronic,
        )

        self.session.add(condition)
        await self.session.flush()
        await self.session.refresh(condition)

        return condition

    async def get_ai_profile(self, id: int) -> Optional[dict]:
        """
        Get patient profile optimized for Mortarium AI

        Args:
            id: Patient ID

        Returns:
            AI-optimized profile dictionary
        """
        patient = await self.get_by_id_with_relations(
            id,
            include_allergies=True,
            include_conditions=True,
            include_insurances=False,
            include_consultations=False,
        )

        if not patient:
            return None

        # Calculate age
        age = None
        if patient.date_of_birth:
            from datetime import date

            today = date.today()
            age = (
                today.year
                - patient.date_of_birth.year
                - (
                    (today.month, today.day)
                    < (patient.date_of_birth.month, patient.date_of_birth.day)
                )
            )

        return {
            "id": patient.id,
            "full_name": patient.full_name,
            "age": age,
            "gender": patient.gender,
            "allergies": [a.allergen_name for a in patient.allergies],
            "conditions": [c.condition_name for c in patient.conditions],
            "blood_type": patient.blood_type,
            "loyalty_tier": patient.loyalty_tier,
            "total_purchases": patient.total_purchases,
            "visit_count": patient.visit_count,
            "last_visit_date": (
                patient.last_visit_date.isoformat() if patient.last_visit_date else None
            ),
            "preferred_language": patient.preferred_language,
        }
