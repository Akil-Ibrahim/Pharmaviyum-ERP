"""Deterministic POS sale and payment state transitions."""


class POSStateTransitionError(ValueError):
    """Raised when a POS state transition is not allowed."""


SALE_PENDING = "pending"
SALE_COMPLETED = "completed"
PAYMENT_UNPAID = "unpaid"
PAYMENT_PAID = "paid"


def confirm_payment(order, confirmed_at):
    """Move a pending POS order from unpaid to paid and completed.

    Inventory mutation must happen in the same database transaction before
    this transition is committed. The function itself is deliberately
    deterministic and contains no AI-dependent logic.
    """
    if order.status != SALE_PENDING:
        raise POSStateTransitionError(
            f"Sale {order.id} cannot be paid from status {order.status}"
        )
    if order.payment_status != PAYMENT_UNPAID:
        raise POSStateTransitionError(
            f"Sale {order.id} cannot be paid from payment status {order.payment_status}"
        )

    order.payment_status = PAYMENT_PAID
    order.payment_confirmed_at = confirmed_at
    order.status = SALE_COMPLETED
