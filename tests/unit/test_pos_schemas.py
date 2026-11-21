"""Validation tests for POS checkout request contracts."""

import pytest
from pydantic import ValidationError

from src.pharmaviyum.schemas.pos import SaleCreate

pytestmark = pytest.mark.unit


def test_cash_checkout_requires_tendered_amount() -> None:
    with pytest.raises(ValidationError, match="cash_received"):
        SaleCreate(
            pharmacy_id=1,
            idempotency_key="checkout-0001",
            items=[{"product_id": 10, "quantity": 2}],
            payment_method="cash",
        )


def test_cash_checkout_accepts_tendered_amount() -> None:
    payload = SaleCreate(
        pharmacy_id=1,
        idempotency_key="checkout-0002",
        items=[{"product_id": 10, "quantity": 2}],
        payment_method="cash",
        cash_received="25.00",
    )
    assert payload.cash_received == 25


@pytest.mark.parametrize("method", ["card_terminal", "online"])
def test_external_payment_does_not_accept_cash_tender(method: str) -> None:
    with pytest.raises(ValidationError, match="cash_received"):
        SaleCreate(
            pharmacy_id=1,
            idempotency_key="checkout-0003",
            items=[{"product_id": 10, "quantity": 2}],
            payment_method=method,
            cash_received="25.00",
        )


def test_duplicate_product_lines_are_rejected() -> None:
    with pytest.raises(ValidationError, match="only once"):
        SaleCreate(
            pharmacy_id=1,
            idempotency_key="checkout-0004",
            items=[
                {"product_id": 10, "quantity": 1},
                {"product_id": 10, "quantity": 2},
            ],
            payment_method="online",
        )



def test_pos_idempotency_lock_key_is_stable_and_tenant_scoped() -> None:
    from src.pharmaviyum.api.v1.pos import _pos_idempotency_lock_key

    first = _pos_idempotency_lock_key(1, "same-request-key")
    assert first == _pos_idempotency_lock_key(1, "same-request-key")
    assert first != _pos_idempotency_lock_key(2, "same-request-key")
    assert first != _pos_idempotency_lock_key(1, "different-request-key")
    assert -(2**63) <= first < 2**63


def test_inventory_receipt_idempotency_key_is_bounded_after_hashing() -> None:
    from datetime import datetime, timedelta

    from src.pharmaviyum.schemas.pos import InventoryReceiptCreate
    from src.pharmaviyum.services.inventory_movements import (
        movement_idempotency_key,
    )

    payload = InventoryReceiptCreate(
        pharmacy_id=1,
        product_id=1,
        lot_number="LOT-1",
        expiry_date=datetime.utcnow() + timedelta(days=30),
        quantity=1,
        idempotency_key="r" * 128,
    )
    journal_key = movement_idempotency_key(
        "receipt", payload.pharmacy_id, payload.idempotency_key
    )
    assert len(journal_key) <= 128

    with pytest.raises(ValidationError):
        InventoryReceiptCreate(
            pharmacy_id=1,
            product_id=1,
            lot_number="LOT-1",
            expiry_date=datetime.utcnow() + timedelta(days=30),
            quantity=1,
            idempotency_key="r" * 129,
        )


def test_inventory_adjustment_idempotency_key_is_bounded_after_hashing() -> None:
    from src.pharmaviyum.api.v1.pharmacy_entities import InventoryAdjustmentIn
    from src.pharmaviyum.services.inventory_movements import (
        movement_idempotency_key,
    )

    payload = InventoryAdjustmentIn(
        quantity_delta=-1,
        reason="Cycle count correction",
        idempotency_key="a" * 128,
    )
    journal_key = movement_idempotency_key(
        "admin-adjustment", 1, payload.idempotency_key
    )
    assert len(journal_key) <= 128

    with pytest.raises(ValidationError):
        InventoryAdjustmentIn(
            quantity_delta=-1,
            reason="Cycle count correction",
            idempotency_key="a" * 129,
        )
