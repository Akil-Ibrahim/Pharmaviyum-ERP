import pytest

from src.pharmaviyum.api.v1.pharmacy_entities import (
    InventoryIn,
    _validate_inventory_levels,
)
from src.pharmaviyum.models.erp_sync import ERPSyncEvent
from src.pharmaviyum.models.inventory import Inventory


@pytest.mark.unit
def test_inventory_input_rejects_negative_values() -> None:
    with pytest.raises(ValueError):
        InventoryIn(product_id=1, pharmacy_id=1, quantity=-1)

    with pytest.raises(ValueError):
        InventoryIn(product_id=1, pharmacy_id=1, reserved_quantity=-1)

    with pytest.raises(ValueError):
        InventoryIn(product_id=1, pharmacy_id=1, reorder_level=-1)


@pytest.mark.unit
def test_inventory_business_rule_rejects_over_reserved_stock() -> None:
    with pytest.raises(Exception, match="reserved_quantity cannot exceed quantity"):
        _validate_inventory_levels(quantity=5, reserved_quantity=6)


@pytest.mark.unit
def test_inventory_foreign_keys_and_constraints_match_domain() -> None:
    foreign_keys = {
        foreign_key.target_fullname for foreign_key in Inventory.__table__.foreign_keys
    }
    assert "products.id" in foreign_keys
    assert "pharmacies.id" in foreign_keys

    constraint_names = {
        constraint.name
        for constraint in Inventory.__table__.constraints
        if constraint.name
    }
    assert "uq_inventory_product_pharmacy_lot" in constraint_names
    assert "ck_inventory_reserved_lte_quantity" in constraint_names


@pytest.mark.unit
def test_erp_sync_event_uses_cascading_integration_foreign_key() -> None:
    foreign_keys = {
        foreign_key.target_fullname: foreign_key.ondelete
        for foreign_key in ERPSyncEvent.__table__.foreign_keys
    }
    assert foreign_keys["erp_integrations.id"] == "CASCADE"
