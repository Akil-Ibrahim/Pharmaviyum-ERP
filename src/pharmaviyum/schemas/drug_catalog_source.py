from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ReviewStatus = Literal["pending_review", "approved", "rejected", "duplicate"]


class DrugCatalogSourceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_name: str = Field(min_length=1, max_length=50)
    source_record_id: str = Field(min_length=1, max_length=150)
    source_version: str = Field(min_length=1, max_length=100)
    source_url: str | None = Field(default=None, max_length=500)
    license_terms: str | None = Field(default=None, max_length=500)
    extracted_at: datetime
    normalized_payload: dict | None = None


class DrugCatalogSourceReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_status: Literal["approved", "rejected", "duplicate"]
    matched_drug_reference_id: int | None = Field(default=None, gt=0)
    matched_medicinal_product_id: int | None = Field(default=None, gt=0)
    create_new: bool = False
    match_confidence: Decimal | None = Field(default=None, ge=0, le=1)
    review_notes: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_match_target(self):
        has_reference = self.matched_drug_reference_id is not None
        has_product = self.matched_medicinal_product_id is not None
        if has_reference and has_product:
            raise ValueError("Choose one match target or create_new, not both")
        if has_reference and self.create_new or has_product and self.create_new:
            raise ValueError("Choose an existing match or create_new, not both")
        if self.review_status == "approved" and not (
            has_reference or has_product or self.create_new
        ):
            raise ValueError("Approved records require a match target or create_new")
        if self.review_status == "duplicate" and not (has_reference or has_product):
            raise ValueError("Duplicate records require a match target")
        if self.review_status == "rejected" and (
            has_reference or has_product or self.create_new
        ):
            raise ValueError("Rejected records cannot retain a match target or create a product")
        if self.review_status == "duplicate" and self.create_new:
            raise ValueError("Duplicate records cannot create a new catalog product")
        return self


class DrugCatalogSourceResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_name: str
    source_record_id: str
    source_version: str
    source_url: str | None
    license_terms: str | None
    extracted_at: datetime
    normalized_payload: dict | None
    review_status: ReviewStatus
    match_confidence: Decimal | None
    matched_drug_reference_id: int | None
    matched_medicinal_product_id: int | None
    reviewed_by_user_id: int | None
    reviewed_at: datetime | None
    review_notes: str | None
    created_at: datetime
    updated_at: datetime
