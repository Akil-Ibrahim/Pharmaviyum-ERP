"""Integration tests for sellable pharmacy product search."""

import pytest

from src.pharmaviyum.models.product import Product


@pytest.mark.integration
async def test_product_search_matches_strength_and_dosage_form(
    authenticated_client, test_db
):
    product = Product(
        name="Example Medicine",
        sku="MED-SEARCH-001",
        dosage_strength="20 mg",
        dosage_form="capsule",
        price=1.0,
        stock=0,
        is_active=True,
    )
    test_db.add(product)
    await test_db.flush()

    strength_result = await authenticated_client.get(
        "/api/v1/products/search", params={"q": "20 mg"}
    )
    assert strength_result.status_code == 200, strength_result.text
    assert any(item["sku"] == product.sku for item in strength_result.json())

    form_result = await authenticated_client.get(
        "/api/v1/products/search", params={"q": "capsule"}
    )
    assert form_result.status_code == 200, form_result.text
    assert any(item["sku"] == product.sku for item in form_result.json())
