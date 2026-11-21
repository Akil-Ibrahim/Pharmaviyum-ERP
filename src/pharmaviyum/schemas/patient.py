from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PatientBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=8, max_length=20)
    email: Optional[EmailStr] = None
    city: Optional[str] = Field(default=None, max_length=100)
    country: str = Field(default="US", min_length=2, max_length=2)
    customer_category: str = Field(default="General", max_length=50)
    loyalty_tier: str = Field(default="Bronze", max_length=50)
    loyalty_points: int = Field(default=0, ge=0)
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class PatientCreate(PatientBase):
    """Schema for creating a patient."""


class PatientUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    phone: Optional[str] = Field(default=None, min_length=8, max_length=20)
    email: Optional[EmailStr] = None
    city: Optional[str] = Field(default=None, max_length=100)
    country: Optional[str] = Field(default=None, min_length=2, max_length=2)
    customer_category: Optional[str] = Field(default=None, max_length=50)
    loyalty_tier: Optional[str] = Field(default=None, max_length=50)
    loyalty_points: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class PatientPurchaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    receipt_number: str
    category: str
    product_id: int | None = None
    batch_id: int | None = None
    batch_number: str | None = None
    expiry_date: date | None = None
    product_name: str | None = None
    quantity: int
    dispensed_packs: int = 1
    dispensed_blisters: int = 0
    dispensed_units: int = 0
    unit_price: float
    total_amount: float
    prescription_required: bool
    purchased_at: datetime


class PatientConditionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    condition_name: str
    icd10_code: str | None = None
    severity: str
    status: str
    is_chronic: bool
    diagnosis_date: date | None = None
    treatment_notes: str | None = None
    current_medications: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class PatientAllergyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    allergen_type: str
    allergen_name: str
    severity: str
    reaction: str | None = None
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class PatientInsuranceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider_name: str
    policy_number: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PatientConsultationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class PatientSummaryResponse(PatientBase):
    """Minimum-necessary demographic and operational patient representation."""

    id: int
    visit_count: int = Field(default=0, ge=0)
    full_name: str = Field(..., max_length=200)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PatientResponse(PatientSummaryResponse):
    """Legacy broad patient representation; avoid for new API contracts."""

    conditions: list[PatientConditionResponse] = Field(default_factory=list)
    allergies: list[PatientAllergyResponse] = Field(default_factory=list)
    insurances: list[PatientInsuranceResponse] = Field(default_factory=list)
    consultations: list[PatientConsultationResponse] = Field(default_factory=list)
    purchases: list[PatientPurchaseResponse] = Field(default_factory=list)


class PatientListResponse(PatientSummaryResponse):
    """Patient list representation; intentionally excludes clinical relations."""


class PatientAIProfile(BaseModel):
    """Purpose-bound clinical safety context for an authorized AI workflow."""

    patient_id: int
    allergies: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
