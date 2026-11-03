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
    with pytest.raises(
        ValidationError, match="require an existing match or a new catalog entry"
    ):
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


def test_approved_review_can_create_a_new_catalog_entry() -> None:
    payload = DrugCatalogSourceReview(
        review_status="approved",
        create_catalog_entry=True,
        review_notes="Verified source data.",
    )

    assert payload.create_catalog_entry is True
    assert payload.matched_drug_reference_id is None
    assert payload.matched_medicinal_product_id is None


def test_new_catalog_entry_cannot_be_marked_duplicate() -> None:
    with pytest.raises(ValidationError, match="Only approved records"):
        DrugCatalogSourceReview(
            review_status="duplicate",
            create_catalog_entry=True,
            matched_medicinal_product_id=42,
        )


def test_new_catalog_entry_cannot_also_select_existing_match() -> None:
    with pytest.raises(ValidationError, match="cannot also select an existing match"):
        DrugCatalogSourceReview(
            review_status="approved",
            create_catalog_entry=True,
            matched_drug_reference_id=10,
        )
