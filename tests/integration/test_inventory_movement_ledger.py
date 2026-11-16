"""Integration tests for the transactional inventory movement service."""

from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

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
async def test_inventory_movement_rejects_idempotency_key_reuse_with_new_command(
    test_db,
):
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


@pytest.mark.integration
async def test_concurrent_same_movement_key_applies_balance_once(test_db, test_engine):
    pharmacy, _product, lot = await _inventory_fixture(test_db)
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async def apply_once():
        async with session_factory() as session:
            movement = await apply_inventory_movement(
                session,
                inventory_id=lot.id,
                pharmacy_id=pharmacy.id,
                movement_type="stock_adjustment",
                quantity_delta=-1,
                reserved_delta=0,
                actor_type="system",
                actor_user_id=None,
                reason="Concurrent idempotency test",
                idempotency_key="movement-concurrent-same-key-0001",
            )
            await session.commit()
            return movement.id

    movement_ids = await asyncio.gather(apply_once(), apply_once())
    assert movement_ids[0] == movement_ids[1]

    await test_db.refresh(lot)
    assert lot.quantity == 9
    count = await test_db.scalar(
        select(func.count())
        .select_from(InventoryMovement)
        .where(InventoryMovement.pharmacy_id == pharmacy.id)
    )
    assert count == 1


@pytest.mark.integration
async def test_concurrent_distinct_adjustments_cannot_oversell_same_lot(
    test_db, test_engine
):
    pharmacy, _product, lot = await _inventory_fixture(test_db)
    session_factory = async_sessionmaker(
        test_engine, expire_on_commit=False
    )

    async def attempt(key: str):
        async with session_factory() as session:
            try:
                await apply_inventory_movement(
                    session,
                    inventory_id=lot.id,
                    pharmacy_id=pharmacy.id,
                    movement_type="stock_adjustment",
                    quantity_delta=-7,
                    reserved_delta=0,
                    actor_type="system",
                    actor_user_id=None,
                    reason="Concurrent oversell test",
                    idempotency_key=key,
                )
                await session.commit()
                return "applied"
            except InventoryMovementConflict:
                await session.rollback()
                return "rejected"

    outcomes = await asyncio.gather(
        attempt("movement-concurrent-distinct-0001"),
        attempt("movement-concurrent-distinct-0002"),
    )
    assert sorted(outcomes) == ["applied", "rejected"]

    await test_db.refresh(lot)
    assert lot.quantity == 3
    count = await test_db.scalar(
        select(func.count())
        .select_from(InventoryMovement)
        .where(InventoryMovement.pharmacy_id == pharmacy.id)
    )
    assert count == 1


@pytest.mark.integration
@pytest.mark.parametrize(
    ("movement_type", "quantity_delta", "reserved_delta"),
    [
        ("goods_receipt", -1, 0),
        ("accepted_return", 0, 0),
        ("transfer_in", 1, 1),
        ("opening_balance", -1, 0),
        ("cash_sale", 1, 0),
        ("write_off", 0, 0),
        ("expiry_disposal", -1, 1),
        ("transfer_out", 1, 0),
        ("payment_reservation", 1, 1),
        ("payment_reservation", 0, -1),
        ("payment_settlement", -1, 0),
        ("payment_settlement", 0, -1),
        ("payment_failure", 0, 1),
        ("sale_cancellation", -1, -1),
        ("stock_adjustment", 0, 1),
        ("unknown_type", 1, 0),
    ],
)
async def test_inventory_movement_rejects_type_delta_mismatch(
    test_db, movement_type, quantity_delta, reserved_delta
):
    pharmacy, _product, lot = await _inventory_fixture(test_db)
    with pytest.raises(InventoryMovementConflict):
        await apply_inventory_movement(
            test_db,
            inventory_id=lot.id,
            pharmacy_id=pharmacy.id,
            movement_type=movement_type,
            quantity_delta=quantity_delta,
            reserved_delta=reserved_delta,
            actor_type="system",
            actor_user_id=None,
            reason="Invalid movement semantics test",
            idempotency_key=f"invalid-semantics-{movement_type}-{quantity_delta}-{reserved_delta}",
        )


@pytest.mark.integration
async def test_database_rejects_movement_type_delta_mismatch(test_db):
    from sqlalchemy.exc import IntegrityError

    pharmacy, product, lot = await _inventory_fixture(test_db)
    test_db.add(
        InventoryMovement(
            pharmacy_id=pharmacy.id,
            inventory_id=lot.id,
            product_id=product.id,
            movement_type="goods_receipt",
            quantity_delta=-1,
            reserved_delta=0,
            quantity_before=10,
            quantity_after=9,
            reserved_before=0,
            reserved_after=0,
            actor_type="system",
            actor_user_id=None,
            reason="Direct database constraint test",
            idempotency_key="direct-invalid-goods-receipt-0001",
        )
    )
    with pytest.raises(IntegrityError):
        await test_db.flush()
    await test_db.rollback()
