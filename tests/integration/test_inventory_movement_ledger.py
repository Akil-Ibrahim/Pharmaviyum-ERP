"""Integration tests for the transactional inventory movement service."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from src.pharmaviyum.models.inventory import Inventory
from src.pharmaviyum.models.inventory_movement import InventoryMovement
from src.pharmaviyum.models.pharmacy import Pharmacy
from src.pharmaviyum.models.product import Product
from src.pharmaviyum.services.inventory_movements import (
    InventoryMovementConflict,
    apply_inventory_movement,
)


async def _inventory_fixture(test_db):
    pharmacy = Pharmacy(name="Movement Test Pharmacy", code="MOVEMENT-TEST")
    product = Product(
        name="Movement Test Product",
        sku="MOVEMENT-TEST-001",
        price=1.25,
        stock=0,
        is_active=True,
    )
    test_db.add_all([pharmacy, product])
    await test_db.flush()
    lot = Inventory(
        product_id=product.id,
        pharmacy_id=pharmacy.id,
        quantity=10,
        reserved_quantity=0,
        lot_number="MOVEMENT-LOT-001",
    )
    test_db.add(lot)
    await test_db.flush()
    await test_db.commit()
    return pharmacy, product, lot


@pytest.mark.integration
async def test_inventory_movement_is_atomic_and_idempotent(test_db):
    pharmacy, _product, lot = await _inventory_fixture(test_db)

    movement = await apply_inventory_movement(
        test_db,
        inventory_id=lot.id,
        pharmacy_id=pharmacy.id,
        movement_type="stock_adjustment",
        quantity_delta=-2,
        reserved_delta=0,
        actor_type="system",
        actor_user_id=None,
        reason="Integration test adjustment",
        idempotency_key="movement-adjustment-replay-0001",
        reference_type="test",
        reference_id="adjustment-1",
    )
    await test_db.commit()

    replay = await apply_inventory_movement(
        test_db,
        inventory_id=lot.id,
        pharmacy_id=pharmacy.id,
        movement_type="stock_adjustment",
        quantity_delta=-2,
        reserved_delta=0,
        actor_type="system",
        actor_user_id=None,
        reason="Integration test adjustment",
        idempotency_key="movement-adjustment-replay-0001",
        reference_type="test",
        reference_id="adjustment-1",
    )
    assert replay.id == movement.id

    persisted_lot = await test_db.get(Inventory, lot.id)
    assert persisted_lot is not None
    assert persisted_lot.quantity == 8
    assert persisted_lot.reserved_quantity == 0
    count = await test_db.scalar(
        select(func.count())
        .select_from(InventoryMovement)
        .where(InventoryMovement.pharmacy_id == pharmacy.id)
    )
    assert count == 1


@pytest.mark.integration
async def test_inventory_movement_rejects_idempotency_key_reuse_with_new_command(test_db):
    pharmacy, _product, lot = await _inventory_fixture(test_db)
    kwargs = {
        "db": test_db,
        "inventory_id": lot.id,
        "pharmacy_id": pharmacy.id,
        "movement_type": "stock_adjustment",
        "quantity_delta": -1,
        "reserved_delta": 0,
        "actor_type": "system",
        "actor_user_id": None,
        "reason": "Count correction",
        "idempotency_key": "movement-adjustment-conflict-0001",
        "reference_type": "test",
        "reference_id": "adjustment-2",
    }
    await apply_inventory_movement(**kwargs)
    await test_db.commit()

    with pytest.raises(InventoryMovementConflict, match="different movement"):
        await apply_inventory_movement(**{**kwargs, "quantity_delta": -2})


@pytest.mark.integration
async def test_inventory_movement_rejects_reservation_above_on_hand(test_db):
    pharmacy, _product, lot = await _inventory_fixture(test_db)

    with pytest.raises(
        InventoryMovementConflict, match="Reserved quantity cannot exceed"
    ):
        await apply_inventory_movement(
            test_db,
            inventory_id=lot.id,
            pharmacy_id=pharmacy.id,
            movement_type="payment_reservation",
            quantity_delta=0,
            reserved_delta=11,
            actor_type="system",
            actor_user_id=None,
            reason="Payment reservation test",
            idempotency_key="movement-reservation-invalid-0001",
        )

    persisted_lot = await test_db.get(Inventory, lot.id)
    assert persisted_lot is not None
    assert persisted_lot.quantity == 10
    assert persisted_lot.reserved_quantity == 0
