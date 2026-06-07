from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)
    email: Optional[EmailStr] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[EmailStr] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
