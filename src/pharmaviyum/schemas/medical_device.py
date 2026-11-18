"""Public response schemas for the medical-device reference catalog."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class MedicalDeviceIdentifierResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    identifier_type: str
    identifier_value: str
    issuing_agency: str | None = None
    is_primary: bool = False


class MedicalDeviceAuthorizationResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    country: str
    authorization_id: str
    authorization_type: str | None = None
    status: str | None = None
    risk_class: str | None = None
    effective_date: date | None = None
    end_date: date | None = None
    source_updated_at: date | None = None


class MedicalDeviceSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_name: str
    source_record_id: str
    country: str
    name: str
    brand_name: str | None = None
    model: str | None = None
    manufacturer: str | None = None
    manufacturer_country: str | None = None
    device_type: str | None = None
    risk_class: str | None = None
    intended_purpose: str | None = None
    regulatory_status: str | None = None
    source_updated_at: date | None = None
    identifiers: list[MedicalDeviceIdentifierResult] = Field(default_factory=list)
    authorizations: list[MedicalDeviceAuthorizationResult] = Field(default_factory=list)
