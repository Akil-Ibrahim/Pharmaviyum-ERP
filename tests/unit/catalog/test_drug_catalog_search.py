"""Regression tests for origin-neutral reference-catalog search."""

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
    assert "medicinal_product_ingredients.ingredient_name" in sql
    assert "teva" not in sql
    assert "israel" not in sql


@pytest.mark.parametrize(
    ("kwargs", "description"),
    [
        ({"brand_name": "Teva"}, "Teva brand"),
        ({"brand_name": "TevaCare"}, "Teva-derived brand"),
        ({"manufacturer": "Teva Pharmaceutical Industries"}, "Teva manufacturer"),
        ({"brand_name": "ExampleMed", "authorization_country": "Israel"}, "Israeli authorization"),
        ({"brand_name": "ExampleMed", "authorization_country": "IL"}, "IL country code"),
        ({"brand_name": "ExampleMed", "manufacturer_country": "ISR"}, "Israeli manufacturer"),
        ({"payload": {"country_of_origin": "IL"}}, "nested origin metadata"),
    ],
)
def test_origin_never_excludes_catalog_entries(
    kwargs: dict, description: str, monkeypatch
) -> None:
    # Even legacy callers setting the compatibility flag cannot re-enable filtering.
    monkeypatch.setattr(catalog_exclusions, "CATALOG_EXCLUSIONS_ENABLED", True)
    assert is_excluded_catalog_entry(**kwargs) is False


def test_reference_and_pharmacy_queries_have_no_origin_exclusion_predicates() -> None:
    assert allowed_medicinal_product_conditions() == ()
    assert allowed_pharmacy_product_conditions() == ()
