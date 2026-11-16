"""Transactional write service for pharmacy inventory movements."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.pharmaviyum.models.inventory import Inventory
from src.pharmaviyum.models.inventory_movement import InventoryMovement


class InventoryMovementConflict(ValueError):
    """Raised when a movement violates stock invariants or idempotency."""


async def apply_inventory_movement(
    db: AsyncSession,
    *,
    inventory_id: int,
    pharmacy_id: int,
    movement_type: str,
    quantity_delta: int,
    reserved_delta: int,
    actor_type: str,
    actor_user_id: int | None,
    reason: str,
    idempotency_key: str,
    reference_type: str | None = None,
    reference_id: str | None = None,
    correlation_id: str | None = None,
) -> InventoryMovement:
    """Apply one balance delta and append its journal row in the caller's transaction.

    The caller owns commit/rollback so sale/payment/outbox transitions can remain
    atomic with the inventory movement. A repeated key with the same immutable
    command returns the existing movement; a different command is rejected.
    """
    idempotency_key = idempotency_key.strip()
    reason = reason.strip()
    if not idempotency_key:
        raise InventoryMovementConflict("An idempotency key is required")
    if not reason:
        raise InventoryMovementConflict("A reason is required")
    if (actor_type == "user") != (actor_user_id is not None):
        raise InventoryMovementConflict("Actor identity does not match actor type")

    # Serialize retries using the pharmacy-scoped key before reading the journal.
    # The unique constraint remains the final database-level idempotency guard.
    await db.execute(
        select(
            func.pg_advisory_xact_lock(
                func.hashtextextended(
                    f"pharmaviyum:inventory-movement:{pharmacy_id}:{idempotency_key}",
                    0,
                )
            )
        )
    )
    existing_result = await db.execute(
        select(InventoryMovement).where(
            InventoryMovement.pharmacy_id == pharmacy_id,
            InventoryMovement.idempotency_key == idempotency_key,
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing is not None:
        same_command = (
            existing.inventory_id == inventory_id
            and existing.movement_type == movement_type
            and existing.quantity_delta == quantity_delta
            and existing.reserved_delta == reserved_delta
            and existing.actor_type == actor_type
            and existing.actor_user_id == actor_user_id
            and existing.reference_type == reference_type
            and existing.reference_id == reference_id
            and existing.reason == reason
            and existing.correlation_id == correlation_id
        )
        if not same_command:
            raise InventoryMovementConflict(
                "Idempotency key was already used for a different movement"
            )
        return existing

    lot_result = await db.execute(
        select(Inventory)
        .where(
            Inventory.id == inventory_id,
            Inventory.pharmacy_id == pharmacy_id,
        )
        .with_for_update()
    )
    lot = lot_result.scalar_one_or_none()
    if lot is None:
        raise InventoryMovementConflict("Inventory lot does not belong to pharmacy")

    quantity_before = lot.quantity
    reserved_before = lot.reserved_quantity
    quantity_after = quantity_before + quantity_delta
    reserved_after = reserved_before + reserved_delta
    if quantity_after < 0 or reserved_after < 0:
        raise InventoryMovementConflict("Inventory balances cannot be negative")
    if reserved_after > quantity_after:
        raise InventoryMovementConflict(
            "Reserved quantity cannot exceed on-hand quantity"
        )
    if quantity_delta == 0 and reserved_delta == 0:
        raise InventoryMovementConflict("A movement must change a balance")

    movement = InventoryMovement(
        pharmacy_id=pharmacy_id,
        inventory_id=lot.id,
        product_id=lot.product_id,
        movement_type=movement_type,
        quantity_delta=quantity_delta,
        reserved_delta=reserved_delta,
        quantity_before=quantity_before,
        quantity_after=quantity_after,
        reserved_before=reserved_before,
        reserved_after=reserved_after,
        actor_type=actor_type,
        actor_user_id=actor_user_id,
        reason=reason,
        reference_type=reference_type,
        reference_id=reference_id,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )
    lot.quantity = quantity_after
    lot.reserved_quantity = reserved_after
    db.add(movement)
    await db.flush()
    return movement
