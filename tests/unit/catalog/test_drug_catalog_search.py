"""Regression tests for reference catalog search fields and strict exclusions."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.pharmaviyum.api.v1.drug_catalog import search_drug_catalog
from src.pharmaviyum.services import catalog_exclusions
from src.pharmaviyum.services.catalog_exclusions import (
    allowed_medicinal_product_conditions,
    allowed_pharmacy_product_conditions,
    is_excluded_catalog_entry,
)


@pytest.mark.asyncio
async def test_search_includes_medicinal_product_strength() -> None:
    scalars = MagicMock()
    scalars.unique.return_value.all.return_value = []
    result = MagicMock()
    result.scalars.return_value = scalars
    db = SimpleNamespace(execute=AsyncMock(return_value=result))

    products = await search_drug_catalog(
        db=db,
        _=SimpleNamespace(id=1, is_superuser=False),
        q="500 mg",
        limit=20,
        country=None,
    )

    assert products == []
    statement = db.execute.await_args.args[0]
    sql = str(statement.compile(compile_kwargs={"literal_binds": True})).lower()
    assert "medicinal_products.strength" in sql


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"brand_name": "Teva"}, True),
        ({"brand_name": "TevaCare"}, True),
        ({"manufacturer": "Teva Pharmaceutical Industries"}, True),
        ({"brand_name": "Generic brand", "authorization_country": "Israel"}, True),
        ({"brand_name": "Generic brand", "authorization_country": "IL - Israel"}, True),
        ({"brand_name": "Generic brand", "manufacturer_country": "ISR (Israel)"}, True),
        (
            {
                "brand_name": "Generic brand",
                "payload": {"country_of_origin": "IL"},
            },
            True,
        ),
        (
            {
                "brand_name": "Generic brand",
                "payload": {"manufacturer_country": "IL"},
            },
            True,
        ),
        (
            {
                "brand_name": "Generic brand",
                "payload": {"country_of_manufacture": "State of Israel"},
            },
            True,
        ),
        (
            {
                "brand_name": "Generic brand",
                "manufacturer": "Example Pharma",
                "authorization_country": "Germany",
            },
            False,
        ),
    ],
)
def test_exclusion_policy_when_enabled(
    kwargs: dict, expected: bool, monkeypatch
) -> None:
    monkeypatch.setattr(catalog_exclusions, "CATALOG_EXCLUSIONS_ENABLED", True)
    assert is_excluded_catalog_entry(**kwargs) is expected


@pytest.mark.parametrize(
    "payload",
    [
        {"manufacturerCountry": "IL"},
        {"metadata": {"countryOfOrigin": "Israel"}},
        {"details": [{"country_of_manufacture": "State of Israel"}]},
    ],
)
def test_excludes_nested_israeli_country_metadata_when_enabled(
    payload: dict, monkeypatch
) -> None:
    monkeypatch.setattr(catalog_exclusions, "CATALOG_EXCLUSIONS_ENABLED", True)
    assert is_excluded_catalog_entry(payload=payload)


def test_does_not_match_teva_as_part_of_another_word(monkeypatch) -> None:
    monkeypatch.setattr(catalog_exclusions, "CATALOG_EXCLUSIONS_ENABLED", True)
    assert not is_excluded_catalog_entry(manufacturer="Whatever Pharmaceutical")


def test_excludes_explicit_manufacturer_country_even_when_authorized_elsewhere(
    monkeypatch,
) -> None:
    monkeypatch.setattr(catalog_exclusions, "CATALOG_EXCLUSIONS_ENABLED", True)
    assert is_excluded_catalog_entry(
        manufacturer="Example Pharma",
        authorization_country="Germany",
        manufacturer_country="IL",
    )


def test_exclusion_policy_is_enabled_by_default() -> None:
    assert catalog_exclusions.CATALOG_EXCLUSIONS_ENABLED is True
    assert is_excluded_catalog_entry(brand_name="Teva")
    assert is_excluded_catalog_entry(authorization_country="Israel")
    assert allowed_medicinal_product_conditions()


def test_catalog_autocomplete_exclusions_are_enabled_by_default() -> None:
    from sqlalchemy import select

    from src.pharmaviyum.models.drug_catalog import MedicinalProduct

    statement = select(MedicinalProduct).where(*allowed_medicinal_product_conditions())
    sql = str(statement.compile(compile_kwargs={"literal_binds": True})).lower()
    assert "medicinal_products.brand_name" in sql
    assert "medicinal_products.manufacturer" in sql
    assert "medicinal_products.manufacturer_country" in sql
    assert "teva" in sql


def test_pos_product_queries_enforce_exclusions_by_default() -> None:
    from sqlalchemy import select

    from src.pharmaviyum.models.product import Product

    statement = select(Product).where(*allowed_pharmacy_product_conditions())
    sql = str(statement.compile(compile_kwargs={"literal_binds": True})).lower()
    assert "products.name" in sql
    assert "products.manufacturer" in sql
    assert "products.manufacturer_country" in sql
    assert "medicinal_products.authorization_country" in sql
    assert "teva" in sql
    assert "israel" in sql


@pytest.mark.unit
def test_global_medicinal_catalog_visibility_enforces_exclusions(monkeypatch) -> None:
    from sqlalchemy import select

    from src.pharmaviyum.models.drug_catalog import MedicinalProduct

    monkeypatch.setattr(catalog_exclusions, "CATALOG_EXCLUSIONS_ENABLED", True)
    statement = select(MedicinalProduct).where(*allowed_medicinal_product_conditions())
    sql = str(statement.compile(compile_kwargs={"literal_binds": True})).lower()
    assert "medicinal_products.brand_name" in sql
    assert "medicinal_products.manufacturer_country" in sql
    assert "teva" in sql
    assert "israel" in sql
