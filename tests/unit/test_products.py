import pytest
from pydantic import ValidationError

from src.pharmaviyum.models.inventory import Inventory
from src.pharmaviyum.models.product import Product
from src.pharmaviyum.schemas.product_schema import ProductCreate, ProductUpdate


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
