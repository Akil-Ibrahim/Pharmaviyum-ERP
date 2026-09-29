"""Deterministic FEFO allocation helpers for pharmacy inventory."""

from collections.abc import Sequence
from datetime import date
from typing import TypedDict


class FEFOBatch(TypedDict):
    id: int
    expiry_date: date | None
    quantity: int


class FEFOAllocation(TypedDict):
    batch_id: int
    quantity: int


def allocate_fefo(
    batches: Sequence[FEFOBatch], requested_quantity: int, *, today: date
) -> list[FEFOAllocation]:
    """Allocate a requested quantity across usable batches in expiry order.

    Expired batches are excluded. Non-expiring stock is considered after dated
    stock. The function is deterministic and fails if total usable stock is
    insufficient; it never skips an earlier usable batch merely because it
    cannot satisfy the whole request by itself.
    """
    if requested_quantity <= 0:
        raise ValueError("requested_quantity must be greater than zero")

    usable = sorted(
        (
            batch
            for batch in batches
            if batch["quantity"] > 0
            and (batch["expiry_date"] is None or batch["expiry_date"] >= today)
        ),
        key=lambda batch: (
            batch["expiry_date"] is None,
            batch["expiry_date"] or date.max,
            batch["id"],
        ),
    )

    remaining = requested_quantity
    allocations: list[FEFOAllocation] = []
    for batch in usable:
        if remaining == 0:
            break
        quantity = min(batch["quantity"], remaining)
        allocations.append({"batch_id": batch["id"], "quantity": quantity})
        remaining -= quantity

    if remaining:
        raise ValueError("insufficient usable FEFO inventory")
    return allocations
