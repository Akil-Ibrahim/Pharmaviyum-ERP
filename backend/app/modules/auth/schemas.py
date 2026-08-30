"""
Pydantic schemas for User authentication.

Schema hierarchy (as in template):
- UserRegister: Public signup (email, password, full_name only)
- UserCreate: Admin creation (all fields, used internally)
- UserPublic: Public response (no password)
- UserUpdate: Admin update
- UserUpdateMe: Self-update (limited fields)
- UpdatePassword: Password change (current + new)
- NewPassword: Reset password (token + new password)
- Token: Login response
- Message: Generic message response
"""
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ============================================================================
# USER SCHEMAS
# ============================================================================

class UserBase(BaseModel):
    """Base user schema with shared fields."""
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False


class UserRegister(BaseModel):
    """
    Schema for public user registration (POST /users/signup).
    
    Intentionally limited fields:
    - No is_superuser (security: cannot self-assign admin)
    - No is_active (always True for new users)
    """
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for admin user creation (POST /users/)."""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema for admin user update (PATCH /users/{id})."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


class UserUpdateMe(BaseModel):
    """Schema for self-update (PATCH /users/me)."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UpdatePassword(BaseModel):
    """Schema for password change (PATCH /users/me/password)."""
    current_password: str = Field(..., min_length=8, max_length=100)
    new_password: str = Field(..., min_length=8, max_length=100)


class UserPublic(BaseModel):
    """Public user schema (no sensitive data)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime


class UsersPublic(BaseModel):
    """Paginated list of users."""
    data: list[UserPublic]
    count: int


# ============================================================================
# AUTH SCHEMAS
# ============================================================================

class Token(BaseModel):
    """OAuth2 token response (matches template structure)."""
    access_token: str
    token_type: str = "bearer"


class NewPassword(BaseModel):
    """Schema for password reset (POST /reset-password)."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


class Message(BaseModel):
    """Generic message response."""
    message: str
