"""
Prescription repository - Data access layer for prescriptions
Best practice 2026: Repository pattern with advanced queries
"""
from typing import Optional
from datetime import datetime, date
from sqlalchemy import select, func, or_, and_, delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.pharmaviyum.core.repository import BaseRepository
from src.pharmaviyum.models.prescriptions import (
    Prescription,
    PrescriptionItem,
    PrescriptionFill,
    MedicationReminder,
)
from src.pharmaviyum.core.logging import get_logger

logger = get_logger(__name__)


class PrescriptionRepository(BaseRepository[Prescription]):
    """
    Prescription repository with advanced query methods
    
    Extends BaseRepository with prescription-specific operations:
    - Search with multiple filters
    - Eager loading of relationships
    - Statistics queries
    - AI-optimized profiles
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with Prescription model"""
        super().__init__(Prescription, session)
    
    async def get_by_id_with_relations(
        self,
        id: int,
        include_items: bool = True,
        include_patient: bool = True,
        include_fills: bool = False,
        include_reminders: bool = False,
    ) -> Optional[Prescription]:
        """
        Get prescription by ID with eager-loaded relationships
        
        Args:
            id: Prescription ID
            include_items: Load prescription items
            include_patient: Load patient relationship
            include_fills: Load fill history
            include_reminders: Load medication reminders
            
        Returns:
            Prescription with relationships or None
        """
        query = select(Prescription).where(Prescription.id == id)
        
        if include_items:
            query = query.options(selectinload(Prescription.items))
        if include_patient:
            query = query.options(selectinload(Prescription.patient))
        if include_fills:
            query = query.options(selectinload(Prescription.fills))
        if include_reminders:
            query = query.options(selectinload(Prescription.reminders))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_prescription_number(
        self,
        prescription_number: str,
    ) -> Optional[Prescription]:
        """
        Get prescription by prescription number
        
        Args:
            prescription_number: Official prescription number
            
        Returns:
            Prescription or None
        """
        result = await self.session.execute(
            select(Prescription).where(
                Prescription.prescription_number == prescription_number
            )
        )
        return result.scalar_one_or_none()
    
    async def search(
        self,
        patient_id: Optional[int] = None,
        status: Optional[str] = None,
        prescription_type: Optional[str] = None,
        is_controlled: Optional[bool] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Prescription], int]:
        """
        Advanced prescription search with multiple filters
        
        Args:
            patient_id: Filter by patient
            status: Filter by status
            prescription_type: Filter by type
            is_controlled: Filter by controlled substance flag
            date_from: Filter by date_issued (from)
            date_to: Filter by date_issued (to)
            skip: Pagination offset
            limit: Pagination limit
            
        Returns:
            Tuple of (prescriptions list, total count)
        """
        # Build query
        query = select(Prescription)
        count_query = select(func.count(Prescription.id))
        
        # Apply filters
        conditions = []
        
        if patient_id:
            conditions.append(Prescription.patient_id == patient_id)
        
        if status:
            conditions.append(Prescription.status == status)
        
        if prescription_type:
            conditions.append(Prescription.prescription_type == prescription_type)
        
        if is_controlled is not None:
            conditions.append(Prescription.is_controlled == is_controlled)
        
        if date_from:
            conditions.append(Prescription.date_issued >= date_from)
        
        if date_to:
            conditions.append(Prescription.date_issued <= date_to)
        
        # Apply conditions
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        # Get total count
        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()
        
        # Apply pagination and ordering
        query = query.offset(skip).limit(limit).order_by(Prescription.date_issued.desc())
        
        # Execute query
        result = await self.session.execute(query)
        prescriptions = list(result.scalars().all())
        
        return prescriptions, total
    
    async def get_active_prescriptions(
        self,
        patient_id: int,
    ) -> list[Prescription]:
        """
        Get active prescriptions for patient
        
        Args:
            patient_id: Patient ID
            
        Returns:
            List of active prescriptions
        """
        result = await self.session.execute(
            select(Prescription)
            .options(selectinload(Prescription.items))
            .where(
                Prescription.patient_id == patient_id,
                Prescription.status.in_(['active', 'filled']),
            )
            .order_by(Prescription.date_issued.desc())
        )
        
        return list(result.scalars().all())
    
    async def get_expiring_prescriptions(
        self,
        days: int = 30,
    ) -> list[Prescription]:
        """
        Get prescriptions expiring within N days
        
        Args:
            days: Number of days to look ahead
            
        Returns:
            List of expiring prescriptions
        """
        from datetime import timedelta
        
        today = date.today()
        cutoff = today + timedelta(days=days)
        
        result = await self.session.execute(
            select(Prescription)
            .options(selectinload(Prescription.patient))
            .where(
                Prescription.status == 'active',
                Prescription.date_expires <= cutoff,
                Prescription.date_expires >= today,
            )
            .order_by(Prescription.date_expires)
        )
        
        return list(result.scalars().all())
    
    async def get_status_stats(self) -> dict:
        """
        Get statistics by prescription status
        
        Returns:
            Dictionary with status counts
        """
        result = await self.session.execute(
            select(
                Prescription.status,
                func.count(Prescription.id),
            )
            .group_by(Prescription.status)
        )
        
        return {status: count for status, count in result.all()}
    
    async def get_type_stats(self) -> dict:
        """
        Get statistics by prescription type
        
        Returns:
            Dictionary with type counts
        """
        result = await self.session.execute(
            select(
                Prescription.prescription_type,
                func.count(Prescription.id),
            )
            .group_by(Prescription.prescription_type)
        )
        
        return {ptype: count for ptype, count in result.all()}
    
    async def get_controlled_substances_count(self) -> int:
        """
        Get count of controlled substance prescriptions
        
        Returns:
            Count of controlled prescriptions
        """
        result = await self.session.execute(
            select(func.count(Prescription.id))
            .where(Prescription.is_controlled == True)
        )
        
        return result.scalar_one()
    
    async def add_item(
        self,
        prescription_id: int,
        medication_name: str,
        quantity_prescribed: float,
        dosage: Optional[str] = None,
        frequency: Optional[str] = None,
        duration: Optional[str] = None,
        **kwargs,
    ) -> PrescriptionItem:
        """
        Add item to prescription
        
        Args:
            prescription_id: Prescription ID
            medication_name: Medication name
            quantity_prescribed: Quantity prescribed
            dosage: Dosage instructions
            frequency: Frequency
            duration: Duration
            **kwargs: Additional fields
            
        Returns:
            Created prescription item
        """
        item = PrescriptionItem(
            prescription_id=prescription_id,
            medication_name=medication_name,
            quantity_prescribed=quantity_prescribed,
            quantity_remaining=quantity_prescribed,
            dosage=dosage,
            frequency=frequency,
            duration=duration,
            **kwargs,
        )
        
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item)
        
        return item
    
    async def create_fill(
        self,
        prescription_id: int,
        prescription_item_id: int,
        quantity_dispensed: float,
        dispense_date: date,
        pharmacist_id: Optional[int] = None,
        **kwargs,
    ) -> PrescriptionFill:
        """
        Create prescription fill record
        
        Args:
            prescription_id: Prescription ID
            prescription_item_id: Prescription item ID
            quantity_dispensed: Quantity dispensed
            dispense_date: Date of dispensing
            pharmacist_id: Pharmacist who dispensed
            **kwargs: Additional fields
            
        Returns:
            Created fill record
        """
        # Determine fill number
        result = await self.session.execute(
            select(func.count(PrescriptionFill.id))
            .where(PrescriptionFill.prescription_item_id == prescription_item_id)
        )
        fill_number = result.scalar_one() + 1
        
        fill = PrescriptionFill(
            prescription_id=prescription_id,
            prescription_item_id=prescription_item_id,
            pharmacist_id=pharmacist_id,
            fill_number=fill_number,
            quantity_dispensed=quantity_dispensed,
            dispense_date=dispense_date,
            **kwargs,
        )
        
        self.session.add(fill)
        await self.session.flush()
        await self.session.refresh(fill)
        
        return fill
    
    async def get_ai_context(self, prescription_id: int) -> Optional[dict]:
        """
        Get prescription context optimized for Mortarium AI
        
        Args:
            prescription_id: Prescription ID
            
        Returns:
            AI-optimized context dictionary
        """
        prescription = await self.get_by_id_with_relations(
            prescription_id,
            include_items=True,
            include_patient=True,
            include_fills=False,
            include_reminders=False,
        )
        
        if not prescription:
            return None
        
        patient = prescription.patient
        
        return {
            "prescription": {
                "id": prescription.id,
                "type": prescription.prescription_type,
                "status": prescription.status,
                "date_issued": prescription.date_issued.isoformat(),
                "diagnosis": prescription.diagnosis,
                "icd10_code": prescription.icd10_code,
                "items": [
                    {
                        "medication_name": item.medication_name,
                        "dosage": item.dosage,
                        "frequency": item.frequency,
                        "duration": item.duration,
                        "quantity_prescribed": item.quantity_prescribed,
                    }
                    for item in prescription.items
                ],
            },
            "patient": {
                "id": patient.id,
                "full_name": patient.full_name,
                "age": self._calculate_age(patient.date_of_birth),
                "gender": patient.gender,
                "allergies": [a.allergen_name for a in patient.allergies] if hasattr(patient, 'allergies') else [],
                "conditions": [c.condition_name for c in patient.conditions] if hasattr(patient, 'conditions') else [],
            },
        }
    
    def _calculate_age(self, dob) -> Optional[int]:
        """Calculate age from date of birth"""
        if not dob:
            return None
        
        from datetime import date
        today = date.today()
        return today.year - dob.year - (
            (today.month, today.day) < (dob.month, dob.day)
        )
