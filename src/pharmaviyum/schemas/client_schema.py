# schemas/client_schema.py - Client Pydantic schemas (single source of truth)
from pydantic import BaseModel, validator
from datetime import datetime
from typing import Optional
from enum import Enum

class ClientSegment(str, Enum):
    NEW = "new"
    REGULAR = "regular"
    VIP = "vip"
    DORMANT = "dormant"
    PRIVILEGED = "privileged"

class ClientBase(BaseModel):
    full_name: str
    phone: str
    email: Optional[str] = None
    birth_date: Optional[datetime] = None
    discount_percent: Optional[float] = 0.0
    is_privileged: Optional[bool] = False
    privilege_type: Optional[str] = None
    # Medical fields for RAG (Mortarium AI)
    chronic_diseases: Optional[str] = None
    allergies: Optional[str] = None
    regular_medications: Optional[str] = None
    address: Optional[str] = None

    @validator('phone')
    def validate_phone(cls, v):
        if not v or len(v) < 10:
            raise ValueError('Phone number must be at least 10 digits')
        return v

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    birth_date: Optional[datetime] = None
    discount_percent: Optional[float] = None
    is_privileged: Optional[bool] = None
    privilege_type: Optional[str] = None
    chronic_diseases: Optional[str] = None
    allergies: Optional[str] = None
    regular_medications: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None

class ClientResponse(BaseModel):
    id: int
    full_name: str
    phone: str
    email: Optional[str] = None
    birth_date: Optional[datetime] = None
    discount_card: Optional[str] = None
    discount_percent: float
    is_privileged: bool
    privilege_type: Optional[str] = None
    chronic_diseases: Optional[str] = None
    allergies: Optional[str] = None
    regular_medications: Optional[str] = None
    address: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_visit: Optional[datetime] = None
    total_purchases: int
    total_spent: float
    segment: Optional[ClientSegment] = None

    class Config:
        from_attributes = True
