"""Unit tests for deterministic POS state transitions."""

from datetime import datetime

import pytest

from src.pharmaviyum.services.pos_state import (
    POSStateTransitionError,
    confirm_payment,
)


class OrderStub:
    def __init__(self, status="pending", payment_status="unpaid"):
        self.id = 1
        self.status = status
        self.payment_status = payment_status
        self.payment_confirmed_at = None


def test_confirm_payment_moves_pending_sale_to_completed() -> None:
    order = OrderStub()
    confirmed_at = datetime(2026, 9, 29, 22, 0, 0)

    confirm_payment(order, confirmed_at)

    assert order.status == "completed"
    assert order.payment_status == "paid"
    assert order.payment_confirmed_at == confirmed_at


@pytest.mark.parametrize(
    ("status", "payment_status"),
    [
        ("completed", "unpaid"),
        ("cancelled", "unpaid"),
        ("pending", "paid"),
    ],
)
def test_confirm_payment_rejects_invalid_transition(
    status: str, payment_status: str
) -> None:
    order = OrderStub(status=status, payment_status=payment_status)

    with pytest.raises(POSStateTransitionError):
        confirm_payment(order, datetime(2026, 9, 29, 22, 0, 0))
