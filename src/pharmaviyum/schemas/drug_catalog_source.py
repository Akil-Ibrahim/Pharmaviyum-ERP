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
    match_confidence: Decimal | None = Field(default=None, ge=0, le=1)
    create_catalog_entry: bool = False
    review_notes: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_match_target(self):
        has_reference = self.matched_drug_reference_id is not None
        has_product = self.matched_medicinal_product_id is not None
        if has_reference and has_product:
            raise ValueError("Choose one match target, not both")
        if self.create_catalog_entry and self.review_status != "approved":
            raise ValueError("Only approved records can create catalog entries")
        if self.create_catalog_entry and (has_reference or has_product):
            raise ValueError("New catalog entries cannot also select an existing match")
        if self.review_status == "approved" and not (
            has_reference or has_product or self.create_catalog_entry
        ):
            raise ValueError(
                "Approved records require an existing match or a new catalog entry"
            )
        if self.review_status == "duplicate" and not (has_reference or has_product):
            raise ValueError("Duplicate records require a match target")
        if self.review_status == "rejected" and (has_reference or has_product):
            raise ValueError("Rejected records cannot retain a match target")
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
