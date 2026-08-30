from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PatientBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=8, max_length=20)
    email: Optional[EmailStr] = None
    city: Optional[str] = Field(default=None, max_length=100)
    country: str = Field(default="VN", max_length=50)
    loyalty_tier: str = Field(default="Bronze", max_length=50)
    loyalty_points: int = Field(default=0, ge=0)
    total_purchases: float = Field(default=0.0, ge=0)
    visit_count: int = Field(default=0, ge=0)
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
    country: Optional[str] = Field(default=None, max_length=50)
    loyalty_tier: Optional[str] = Field(default=None, max_length=50)
    loyalty_points: Optional[int] = Field(default=None, ge=0)
    total_purchases: Optional[float] = Field(default=None, ge=0)
    visit_count: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class PatientResponse(PatientBase):
    id: int
    full_name: str = Field(..., max_length=200)
    created_at: datetime
    updated_at: datetime

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
    loyalty_tier: str
    loyalty_points: int = 0
    total_purchases: float = 0.0
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
    country: str = "VN"
    loyalty_tier: str = "Bronze"
    allergies: list[str] = []
    conditions: list[str] = []
    insurances: list[str] = []
    risk_summary: str = ""

    model_config = ConfigDict(from_attributes=True)
