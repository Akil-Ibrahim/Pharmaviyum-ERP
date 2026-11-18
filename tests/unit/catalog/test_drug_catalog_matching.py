from types import SimpleNamespace

import pytest

from src.pharmaviyum.services.drug_catalog_matching import suggest_matches


def _reference():
    product = SimpleNamespace(
        id=22,
        brand_name="ExampleMed",
        strength="200 mg",
        dosage_form="Tablet",
        route="Oral use",
        authorization_country="Germany",
    )
    return SimpleNamespace(
        id=11,
        inn_name="ibuprofen",
        ingredients=[SimpleNamespace(ingredient_name="ibuprofen")],
        medicinal_products=[product],
    )


def test_exact_ingredient_and_product_attributes_rank_product_first():
    matches = suggest_matches(
        {
            "ingredient": "Ibuprofen",
            "product_name": "ExampleMed",
            "strength": "200 MG",
            "dosage_form": "Tablet",
            "route": "Oral use",
            "country": "Germany",
        },
        [_reference()],
    )

    assert matches[0]["target_type"] == "medicinal_product"
    assert matches[0]["medicinal_product_id"] == 22
    assert matches[0]["confidence"] == 1.0
    assert "active ingredient: 100%" in matches[0]["reasons"]
    assert "strength: 100%" in matches[0]["reasons"]


def test_brand_mismatch_does_not_override_ingredient_match():
    matches = suggest_matches(
        {"ingredient_name": "ibuprofen", "brand_name": "UnrelatedBrand"},
        [_reference()],
    )

    assert matches
    product_match = next(
        item for item in matches if item["target_type"] == "medicinal_product"
    )
    assert product_match["confidence"] < 1.0
    assert "brand: 100%" not in product_match["reasons"]


def test_combination_product_matches_only_with_complete_composition():
    reference = _reference()
    reference.medicinal_products[0].ingredients = [
        SimpleNamespace(ingredient_name="ibuprofen"),
        SimpleNamespace(ingredient_name="acetaminophen"),
    ]

    matches = suggest_matches(
        {
            "ingredient_name": "ibuprofen",
            "ingredients": [
                {"ingredient_name": "ibuprofen"},
                {"ingredient_name": "acetaminophen"},
            ],
            "brand_name": "ExampleMed",
            "strength": "200 mg + 325 mg",
            "dosage_form": "Tablet",
            "route": "Oral use",
            "country": "Germany",
        },
        [reference],
    )

    product_match = next(
        item for item in matches if item["target_type"] == "medicinal_product"
    )
    assert product_match["confidence"] == 1.0


def test_unrelated_ingredient_returns_no_candidates():
    assert (
        suggest_matches(
            {"ingredient": "amoxicillin", "product_name": "ExampleMed"},
            [_reference()],
        )
        == []
    )


def test_missing_ingredient_returns_no_candidates():
    assert suggest_matches({"product_name": "ExampleMed"}, [_reference()]) == []


def test_source_payload_does_not_mutate_catalog_objects():
    reference = _reference()
    original_brand = reference.medicinal_products[0].brand_name

    suggest_matches(
        {"ingredient": "ibuprofen", "brand_name": "Changed"},
        [reference],
    )

    assert reference.medicinal_products[0].brand_name == original_brand


def test_rank_reference_ids_keeps_fuzzy_candidates_and_bounds_hydration():
    from src.pharmaviyum.services.drug_catalog_matching import rank_reference_ids

    reference_rows = [(1, "ibuprofen"), (2, "amoxicillin"), (3, "ibuprofeno")]
    ingredient_rows = [(3, "ibuprofeno")]
    ranked = rank_reference_ids(
        {"ingredient": "ibuprofin"},
        reference_rows,
        ingredient_rows,
        limit=1,
    )

    assert ranked == [1]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("brand_name", "Teva"),
        ("authorization_country", "Israel"),
        ("manufacturer_country", "IL"),
    ],
)
def test_reference_matching_does_not_exclude_manufacturer_or_country(field, value):
    reference = _reference()
    setattr(reference.medicinal_products[0], field, value)

    matches = suggest_matches(
        {"ingredient_name": "ibuprofen", "brand_name": "ExampleMed"},
        [reference],
    )

    assert matches
    assert any(item["target_type"] == "medicinal_product" for item in matches)
    assert any(item["medicinal_product_id"] == 22 for item in matches)
