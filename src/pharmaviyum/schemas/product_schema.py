from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    sku: str = Field(min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=1000)
    dosage_strength: str | None = Field(default=None, max_length=100)
    dosage_form: str | None = Field(default=None, max_length=50)
    units_per_pack: int = Field(default=1, gt=0)
    package_type: str = Field(default="pack", max_length=50)
    blisters_per_pack: int = Field(default=0, ge=0)
    units_per_blister: int = Field(default=0, ge=0)
    manufacturer: str | None = Field(default=None, max_length=200)
    inn_name: str | None = Field(default=None, max_length=200)
    atc_code: str | None = Field(default=None, max_length=20)
    regulatory_id: str | None = Field(default=None, max_length=50)
    gtin: str | None = Field(default=None, min_length=8, max_length=14)
    barcode: str | None = Field(default=None, max_length=64)
    halal_status: str = Field(default="unknown", pattern="^(halal|haram|unknown)$")
    halal_standard: str | None = Field(default=None, max_length=128)
    halal_evidence: dict = Field(default_factory=dict)
    storage_temperature_min: float | None = None
    storage_temperature_max: float | None = None
    storage_location_type: str = Field(
        default="shelf", pattern="^(shelf|refrigerator|special_storage)$"
    )
    storage_instructions: str | None = Field(default=None, max_length=500)
    price: float = Field(default=0.0, ge=0)
    # Kept for backward compatibility; per-pharmacy stock belongs to Inventory.
    stock: int = Field(default=0, ge=0)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    dosage_strength: str | None = Field(default=None, max_length=100)
    dosage_form: str | None = Field(default=None, max_length=50)
    units_per_pack: int | None = Field(default=None, gt=0)
    package_type: str | None = Field(default=None, max_length=50)
    blisters_per_pack: int | None = Field(default=None, ge=0)
    units_per_blister: int | None = Field(default=None, ge=0)
    manufacturer: str | None = Field(default=None, max_length=200)
    inn_name: str | None = Field(default=None, max_length=200)
    atc_code: str | None = Field(default=None, max_length=20)
    regulatory_id: str | None = Field(default=None, max_length=50)
    gtin: str | None = Field(default=None, min_length=8, max_length=14)
    barcode: str | None = Field(default=None, max_length=64)
    halal_status: str | None = Field(default=None, pattern="^(halal|haram|unknown)$")
    halal_standard: str | None = Field(default=None, max_length=128)
    halal_evidence: dict | None = None
    storage_temperature_min: float | None = None
    storage_temperature_max: float | None = None
    storage_location_type: str | None = Field(
        default=None, pattern="^(shelf|refrigerator|special_storage)$"
    )
    storage_instructions: str | None = Field(default=None, max_length=500)
    price: float | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ProductResponse(BaseModel):
    id: int
    name: str
    sku: str
    description: str | None = None
    dosage_strength: str | None = None
    dosage_form: str | None = None
    units_per_pack: int = 1
    package_type: str = "pack"
    blisters_per_pack: int = 0
    units_per_blister: int = 0
    manufacturer: str | None = None
    inn_name: str | None = None
    atc_code: str | None = None
    regulatory_id: str | None = None
    gtin: str | None = None
    barcode: str | None = None
    halal_status: str = "unknown"
    halal_standard: str | None = None
    halal_evidence: dict = {}
    storage_temperature_min: float | None = None
    storage_temperature_max: float | None = None
    storage_location_type: str = "shelf"
    storage_instructions: str | None = None
    price: float
    stock: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
