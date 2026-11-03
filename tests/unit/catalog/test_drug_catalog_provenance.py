"""Tests for external drug catalog provenance constraints."""

from src.pharmaviyum.models.drug_catalog import DrugCatalogSourceRecord


def test_source_record_defaults_to_pending_review() -> None:
    status = DrugCatalogSourceRecord.__table__.c.review_status

    assert status.default is not None
    assert status.default.arg == "pending_review"
    assert status.nullable is False


def test_source_identity_is_versioned_and_unique() -> None:
    constraints = DrugCatalogSourceRecord.__table__.constraints
    identity = next(
        constraint
        for constraint in constraints
        if getattr(constraint, "name", None) == "uq_drug_catalog_source_identity"
    )

    assert {column.name for column in identity.columns} == {
        "source_name",
        "source_record_id",
        "source_version",
    }


def test_source_record_has_no_sellable_product_or_inventory_columns() -> None:
    columns = set(DrugCatalogSourceRecord.__table__.columns.keys())

    assert "product_id" not in columns
    assert "inventory_id" not in columns
    assert "price" not in columns
    assert "quantity" not in columns
