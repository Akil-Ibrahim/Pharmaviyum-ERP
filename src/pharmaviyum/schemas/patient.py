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


class PatientResponse(PatientBase):
    """Patient representation with system-managed aggregate fields."""

    id: int
    visit_count: int = Field(default=0, ge=0)
    full_name: str = Field(..., max_length=200)
    created_at: datetime
    updated_at: datetime
    conditions: list[PatientConditionResponse] = []
    allergies: list[PatientAllergyResponse] = []
    insurances: list[PatientInsuranceResponse] = []
    consultations: list[PatientConsultationResponse] = []
    purchases: list[PatientPurchaseResponse] = []

    model_config = ConfigDict(from_attributes=True)


class PatientListResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    full_name: str
    phone: str
    email: Optional[EmailStr] = None
    city: Optional[str] = None
    country: str
    customer_category: str
    loyalty_tier: str
    loyalty_points: int = 0
    visit_count: int = 0
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PatientAIProfile(BaseModel):
    patient_id: int
    full_name: str
    phone: str
    city: Optional[str] = None
    country: str = "US"
    customer_category: str = "General"
    loyalty_tier: str = "Bronze"
    allergies: list[str] = []
    conditions: list[str] = []
    insurances: list[str] = []
    risk_summary: str = ""

    model_config = ConfigDict(from_attributes=True)
