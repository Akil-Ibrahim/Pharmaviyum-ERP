"""Validation tests for POS checkout request contracts."""

import pytest
from pydantic import ValidationError

from src.pharmaviyum.schemas.pos import SaleCreate


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
