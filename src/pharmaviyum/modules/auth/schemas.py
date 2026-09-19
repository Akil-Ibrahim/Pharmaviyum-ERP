"""Pydantic schemas for User authentication."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema with shared fields."""

    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False


class UserRegister(BaseModel):
    """Schema for public user registration."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for admin user creation."""

    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema for admin user update."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


class UserUpdateMe(BaseModel):
    """Schema for self-update."""

    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UpdatePassword(BaseModel):
    """Schema for changing the current password."""

    current_password: str = Field(..., min_length=8, max_length=100)
    new_password: str = Field(..., min_length=8, max_length=100)


class UserPublic(BaseModel):
    """Public user schema (no sensitive data)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime


class UsersPublic(BaseModel):
    """Paginated list of users."""

    data: list[UserPublic]
    count: int


class Token(BaseModel):
    """OAuth2 access/refresh token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Request body for refresh-token rotation."""

    refresh_token: str = Field(..., min_length=1)


class NewPassword(BaseModel):
    """Schema for password reset."""

    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


class Message(BaseModel):
    """Generic message response."""

    message: str
