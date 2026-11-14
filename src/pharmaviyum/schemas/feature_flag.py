"""
Pydantic schemas for feature flags
"""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class FlagType(str, Enum):
    """Feature flag types"""

    BOOLEAN = "boolean"
    PERCENTAGE = "percentage"
    SEGMENT = "segment"
    MULTIVARIATE = "multivariate"


class FeatureFlagCreate(BaseModel):
    """Schema for creating feature flag"""

    key: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9_]+$")
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    flag_type: FlagType = FlagType.BOOLEAN
    enabled: bool = False
    percentage: int = Field(default=0, ge=0, le=100)
    segments: list[str] = Field(default_factory=list)
    variants: dict[str, Any] = Field(default_factory=dict)
    default_value: Any = False


class FeatureFlagUpdate(BaseModel):
    """Schema for updating feature flag"""

    name: Optional[str] = None
    description: Optional[str] = None
    flag_type: Optional[FlagType] = None
    enabled: Optional[bool] = None
    percentage: Optional[int] = Field(None, ge=0, le=100)
    segments: Optional[list[str]] = None
    variants: Optional[dict[str, Any]] = None
    default_value: Optional[Any] = None


class FeatureFlagResponse(BaseModel):
    """Schema for feature flag response"""

    key: str
    name: str
    description: Optional[str] = None
    flag_type: FlagType
    enabled: bool
    percentage: int
    segments: list[str]
    variants: dict[str, Any]
    default_value: Any
    created_at: str
    updated_at: str
    created_by: str


class FeatureFlagListResponse(BaseModel):
    """Schema for feature flag list"""

    flags: list[FeatureFlagResponse]
    total: int


class FeatureFlagStatsResponse(BaseModel):
    """Schema for feature flag statistics"""

    flag_key: str
    enabled_count: int
    disabled_count: int
    total_checks: int
    enabled_percentage: float


class FeatureFlagCheckRequest(BaseModel):
    """Schema for checking feature flag"""

    key: str
    user_id: Optional[str] = None
    user_segment: Optional[str] = None


class FeatureFlagCheckResponse(BaseModel):
    """Schema for feature flag check result"""

    key: str
    enabled: bool
    variant: Optional[Any] = None
