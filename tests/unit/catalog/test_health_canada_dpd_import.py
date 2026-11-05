"""Tests for the Health Canada DPD source normalizer."""

import pytest

from scripts.import_health_canada_dpd import normalize_dpd_records

pytestmark = pytest.mark.unit


def test_normalizer_keeps_current_single_ingredient_products_and_variants() -> None:
    products = [
        {
            "drug_code": 101,
            "drug_identification_number": "01234567",
            "brand_name": "OMEPRAZOLE TEST",
            "descriptor": "",
            "number_of_ais": "1",
            "company_name": "Example Pharma",
            "class_name": "Human",
        },
        {
            "drug_code": 102,
            "drug_identification_number": "07654321",
            "brand_name": "COMBINATION TEST",
            "number_of_ais": "2",
            "company_name": "Example Pharma",
            "class_name": "Human",
        },
        {
            "drug_code": 103,
            "drug_identification_number": "09999999",
            "brand_name": "CANCELLED TEST",
            "number_of_ais": "1",
            "company_name": "Example Pharma",
            "class_name": "Human",
        },
        {
            "drug_code": 104,
            "drug_identification_number": "08888888",
            "brand_name": "TEVA TEST",
            "descriptor": "",
            "number_of_ais": "1",
            "company_name": "Teva Pharmaceutical Industries",
            "class_name": "Human",
        },
        {
            "drug_code": 105,
            "drug_identification_number": "07777777",
            "brand_name": "ISRAEL ORIGIN TEST",
            "descriptor": "",
            "number_of_ais": "1",
            "company_name": "Example Pharma",
            "manufacturer_country": "IL",
            "class_name": "Human",
        },
    ]
    ingredients = [
        {
            "drug_code": 101,
            "ingredient_name": "OMEPRAZOLE",
            "strength": "20",
            "strength_unit": "MG",
        },
        {
            "drug_code": 102,
            "ingredient_name": "INGREDIENT A",
            "strength": "5",
            "strength_unit": "MG",
        },
        {
            "drug_code": 102,
            "ingredient_name": "INGREDIENT B",
            "strength": "10",
            "strength_unit": "MG",
        },
        {
            "drug_code": 103,
            "ingredient_name": "OMEPRAZOLE",
            "strength": "40",
            "strength_unit": "MG",
        },
        {
            "drug_code": 104,
            "ingredient_name": "OMEPRAZOLE",
            "strength": "20",
            "strength_unit": "MG",
        },
        {
            "drug_code": 105,
            "ingredient_name": "OMEPRAZOLE",
            "strength": "20",
            "strength_unit": "MG",
        },
    ]
    forms = [
        {"drug_code": 101, "pharmaceutical_form_name": "Capsule"},
        {"drug_code": 101, "pharmaceutical_form_name": "Delayed-release capsule"},
    ]
    routes = [{"drug_code": 101, "route_of_administration_name": "Oral"}]
    statuses = [
        {"drug_code": 101, "status": "Approved", "history_date": "2025-01-01"},
        {"drug_code": 102, "status": "Marketed", "history_date": "2025-01-01"},
        {
            "drug_code": 103,
            "status": "Cancelled Post Market",
            "history_date": "2025-01-01",
        },
        {
            "drug_code": 104,
            "status": "Approved",
            "history_date": "2025-01-01",
        },
        {
            "drug_code": 105,
            "status": "Approved",
            "history_date": "2025-01-01",
        },
    ]
    packaging = [{"drug_code": 101, "product_information": "100 Capsule Bottle"}]

    rows = normalize_dpd_records(
        products, ingredients, forms, routes, statuses, packaging
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["source_record_id"] == "DPD:101"
    assert row["ingredient_name"] == "OMEPRAZOLE"
    assert row["strength"] == "20 MG"
    assert row["dosage_form"] == "Capsule / Delayed-release capsule"
    assert row["route"] == "Oral"
    assert row["country"] == "CA"
    assert row["regulatory_id"] == "01234567"
    assert row["authorization_status"] == "Approved"


def test_normalizer_rejects_products_without_single_active_ingredient() -> None:
    rows = normalize_dpd_records(
        products=[
            {
                "drug_code": 1,
                "number_of_ais": "1",
                "drug_identification_number": "00000001",
            }
        ],
        ingredients=[],
        forms=[],
        routes=[],
        statuses=[{"drug_code": 1, "status": "Marketed", "history_date": "2025-01-01"}],
        packaging=[],
    )
    assert rows == []
