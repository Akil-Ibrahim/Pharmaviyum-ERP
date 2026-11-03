"""Validation tests for Drug Catalog source review decisions."""

import pytest
from pydantic import ValidationError

from src.pharmaviyum.schemas.drug_catalog_source import DrugCatalogSourceReview


def test_approved_review_requires_exactly_one_match_target():
    with pytest.raises(ValidationError):
        DrugCatalogSourceReview(review_status="approved")

    with pytest.raises(ValidationError):
        DrugCatalogSourceReview(
            review_status="approved",
            matched_drug_reference_id=1,
            matched_medicinal_product_id=2,
        )

    payload = DrugCatalogSourceReview(
        review_status="approved",
        matched_drug_reference_id=1,
        match_confidence="0.95",
    )
    assert payload.matched_drug_reference_id == 1
    assert payload.matched_medicinal_product_id is None


def test_duplicate_review_requires_a_match_target():
    with pytest.raises(ValidationError):
        DrugCatalogSourceReview(review_status="duplicate")

    payload = DrugCatalogSourceReview(
        review_status="duplicate",
        matched_medicinal_product_id=42,
    )
    assert payload.matched_medicinal_product_id == 42


def test_rejected_review_cannot_retain_match_target():
    with pytest.raises(ValidationError):
        DrugCatalogSourceReview(
            review_status="rejected",
            matched_drug_reference_id=1,
        )

    payload = DrugCatalogSourceReview(
        review_status="rejected",
        review_notes="Insufficient provenance",
    )
    assert payload.matched_drug_reference_id is None
    assert payload.match_confidence is None


def test_review_rejects_unknown_fields_and_out_of_range_confidence():
    with pytest.raises(ValidationError):
        DrugCatalogSourceReview(
            review_status="approved",
            matched_drug_reference_id=1,
            match_confidence="1.01",
        )

    with pytest.raises(ValidationError):
        DrugCatalogSourceReview(
            review_status="rejected",
            unexpected="value",
        )
