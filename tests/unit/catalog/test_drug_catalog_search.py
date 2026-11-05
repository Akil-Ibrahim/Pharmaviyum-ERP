"""Regression tests for reference catalog search fields."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.pharmaviyum.api.v1.drug_catalog import search_drug_catalog
from src.pharmaviyum.services.catalog_exclusions import is_excluded_catalog_entry


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
        ({"manufacturer": "Teva Pharmaceutical Industries"}, True),
        ({"brand_name": "Generic brand", "authorization_country": "Israel"}, True),
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
def test_excluded_catalog_entries(kwargs: dict, expected: bool) -> None:
    assert is_excluded_catalog_entry(**kwargs) is expected


@pytest.mark.parametrize(
    "payload",
    [
        {"manufacturerCountry": "IL"},
        {"metadata": {"countryOfOrigin": "Israel"}},
        {"details": [{"country_of_manufacture": "State of Israel"}]},
    ],
)
def test_excludes_nested_israeli_country_metadata(payload: dict) -> None:
    assert is_excluded_catalog_entry(payload=payload)


def test_does_not_match_teva_as_part_of_another_word() -> None:
    assert not is_excluded_catalog_entry(manufacturer="Whatever Pharmaceutical")


def test_excludes_explicit_manufacturer_country_even_when_authorized_elsewhere() -> None:
    assert is_excluded_catalog_entry(
        manufacturer="Example Pharma",
        authorization_country="Germany",
        manufacturer_country="IL",
    )
