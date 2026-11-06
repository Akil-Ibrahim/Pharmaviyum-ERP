from datetime import datetime

import pytest
from pydantic import ValidationError

from src.pharmaviyum.models.inventory import Inventory
from src.pharmaviyum.models.product import Product
from src.pharmaviyum.schemas.product_schema import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)
from src.pharmaviyum.services.catalog_exclusions import (
    allowed_pharmacy_product_conditions,
)


@pytest.mark.unit
def test_product_create_rejects_negative_price_and_stock() -> None:
    with pytest.raises(ValidationError):
        ProductCreate(name="Test", sku="SKU-1", price=-1)

    with pytest.raises(ValidationError):
        ProductCreate(name="Test", sku="SKU-1", stock=-1)


@pytest.mark.unit
def test_product_update_rejects_negative_values() -> None:
    with pytest.raises(ValidationError):
        ProductUpdate(price=-1)

    with pytest.raises(ValidationError):
        ProductUpdate(stock=-1)


@pytest.mark.unit
def test_inventory_schema_constraints_are_declared() -> None:
    constraint_names = {
        constraint.name
        for constraint in Inventory.__table__.constraints
        if constraint.name
    }
    assert "uq_inventory_product_pharmacy_lot" in constraint_names
    assert "ck_inventory_quantity_nonnegative" in constraint_names
    assert "ck_inventory_reserved_nonnegative" in constraint_names
    assert "ck_inventory_reserved_lte_quantity" in constraint_names
    assert "ck_inventory_reorder_level_nonnegative" in constraint_names


@pytest.mark.unit
def test_product_schema_matches_database_invariants() -> None:
    constraint_names = {
        constraint.name
        for constraint in Product.__table__.constraints
        if constraint.name
    }
    assert "ck_products_price_nonnegative" in constraint_names
    assert "ck_products_stock_nonnegative" in constraint_names


@pytest.mark.unit
def test_product_manufacturer_country_is_supported_across_schemas() -> None:
    created = ProductCreate(
        name="Synthetic medicine",
        sku="SYNTH-001",
        manufacturer="Example Pharma",
        manufacturer_country="Germany",
    )
    updated = ProductUpdate(manufacturer_country="France")
    assert created.manufacturer_country == "Germany"
    assert updated.manufacturer_country == "France"

    response = ProductResponse(
        id=1,
        name="Synthetic medicine",
        sku="SYNTH-001",
        manufacturer="Example Pharma",
        manufacturer_country="Germany",
        price=12.5,
        stock=0,
        is_active=True,
        created_at=datetime(2026, 1, 1),
        updated_at=None,
    )
    assert response.manufacturer_country == "Germany"


@pytest.mark.unit
def test_pharmacy_product_visibility_enforces_catalog_exclusions_by_default() -> None:
    from sqlalchemy import select

    conditions = allowed_pharmacy_product_conditions()
    assert conditions

    statement = select(Product).where(*conditions)
    sql = str(statement.compile(compile_kwargs={"literal_binds": True})).lower()
    assert "\nwhere " in sql
    assert "products.name" in sql
    assert "products.manufacturer" in sql
    assert "products.manufacturer_country" in sql
    assert "medicinal_products.authorization_country" in sql
    assert "teva" in sql
    assert "israel" in sql
