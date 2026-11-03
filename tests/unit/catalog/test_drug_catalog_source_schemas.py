"""Validation tests for the external drug source review contract."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.pharmaviyum.schemas.drug_catalog_source import (
    DrugCatalogSourceCreate,
    DrugCatalogSourceReview,
)


def test_source_intake_requires_source_identity_and_extraction_time() -> None:
    payload = DrugCatalogSourceCreate(
        source_name="RxNorm",
        source_record_id="123456",
        source_version="2026-10",
        extracted_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        normalized_payload={"name": "Example"},
    )

    assert payload.source_name == "RxNorm"
    assert payload.source_record_id == "123456"


def test_approved_review_requires_exactly_one_match_target() -> None:
    with pytest.raises(ValidationError, match="require a match target"):
        DrugCatalogSourceReview(review_status="approved")


def test_review_rejects_two_match_targets() -> None:
    with pytest.raises(ValidationError, match="Choose one match target"):
        DrugCatalogSourceReview(
            review_status="approved",
            matched_drug_reference_id=10,
            matched_medicinal_product_id=20,
        )


def test_rejected_review_cannot_keep_a_match_target() -> None:
    with pytest.raises(ValidationError, match="cannot retain a match target"):
        DrugCatalogSourceReview(
            review_status="rejected",
            matched_drug_reference_id=10,
        )


def test_duplicate_review_requires_link_to_existing_catalog_record() -> None:
    payload = DrugCatalogSourceReview(
        review_status="duplicate",
        matched_medicinal_product_id=42,
        match_confidence="0.9900",
        review_notes="Same GTIN and package configuration",
    )

    assert payload.matched_medicinal_product_id == 42
