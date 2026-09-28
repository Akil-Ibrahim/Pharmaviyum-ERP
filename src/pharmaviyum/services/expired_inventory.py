"""Quarantine expired stock and keep a separate inventory ledger."""

from datetime import datetime
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.pharmaviyum.models.audit_log import AuditLog
from src.pharmaviyum.models.expired_inventory import ExpiredInventory
from src.pharmaviyum.models.inventory import Inventory
from src.pharmaviyum.models.inventory_transaction import InventoryTransaction
from src.pharmaviyum.models.product_batch import ProductBatch


async def quarantine_expired_inventory(
    db: AsyncSession,
    *,
    pharmacy_id: int,
    actor_id: int,
    now: datetime | None = None,
) -> int:
    """Move all expired usable stock for a pharmacy into quarantine accounting.

    This operation is idempotent for inventory rows with zero usable quantity:
    a quarantined row cannot be dispensed again.
    """
    now = now or datetime.utcnow()
    today = now.date()
    query = (
        select(Inventory)
        .outerjoin(ProductBatch, Inventory.batch_id == ProductBatch.id)
        .where(
            Inventory.pharmacy_id == pharmacy_id,
            Inventory.quantity > 0,
            or_(
                and_(Inventory.expires_at.is_not(None), Inventory.expires_at < now),
                and_(
                    ProductBatch.id.is_not(None),
                    ProductBatch.expiry_date < today,
                ),
            ),
        )
        .with_for_update()
    )
    result = await db.execute(query)
    inventories = result.scalars().all()

    quarantined_count = 0
    for inventory in inventories:
        quantity = inventory.quantity
        if quantity <= 0:
            continue

        batch = None
        if inventory.batch_id is not None:
            batch = await db.scalar(
                select(ProductBatch)
                .where(ProductBatch.id == inventory.batch_id)
                .with_for_update()
            )

        inventory.quantity = 0
        inventory.reserved_quantity = 0

        if batch is not None:
            batch.available_quantity = max(0, batch.available_quantity - quantity)

        expired = ExpiredInventory(
            pharmacy_id=pharmacy_id,
            inventory_id=inventory.id,
            product_id=inventory.product_id,
            batch_id=inventory.batch_id,
            quantity_units=quantity,
            reason="expired",
            status="quarantined",
            quarantined_at=now,
        )
        db.add(expired)
        await db.flush()

        db.add(
            InventoryTransaction(
                pharmacy_id=pharmacy_id,
                inventory_id=inventory.id,
                product_id=inventory.product_id,
                batch_id=inventory.batch_id,
                transaction_type="expiry_quarantine",
                quantity_delta=-quantity,
                quantity_after=0,
                actor_id=actor_id,
                created_at=now,
            )
        )
        db.add(
            AuditLog(
                actor_id=actor_id,
                actor_type="user",
                action="expiry_quarantine",
                entity="inventory",
                entity_id=inventory.id,
                changes={
                    "pharmacy_id": pharmacy_id,
                    "product_id": inventory.product_id,
                    "batch_id": inventory.batch_id,
                    "quantity_units": quantity,
                    "status": "quarantined",
                },
            )
        )
        quarantined_count += 1

    await db.flush()
    return quarantined_count


async def list_expired_inventory(
    db: AsyncSession,
    *,
    pharmacy_id: int,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Return quarantined/expired stock for pharmacy operations UI."""
    result = await db.execute(
        select(ExpiredInventory, ProductBatch)
        .outerjoin(ProductBatch, ExpiredInventory.batch_id == ProductBatch.id)
        .where(ExpiredInventory.pharmacy_id == pharmacy_id)
        .order_by(ExpiredInventory.quarantined_at.desc())
        .limit(limit)
    )
    rows = []
    for expired, batch in result.all():
        rows.append(
            {
                "id": expired.id,
                "inventory_id": expired.inventory_id,
                "product_id": expired.product_id,
                "batch_id": expired.batch_id,
                "batch_number": batch.batch_number if batch else None,
                "expiry_date": batch.expiry_date if batch else None,
                "quantity_units": expired.quantity_units,
                "reason": expired.reason,
                "status": expired.status,
                "quarantined_at": expired.quarantined_at,
                "disposed_at": expired.disposed_at,
                "disposal_method": expired.disposal_method,
            }
        )
    return rows
