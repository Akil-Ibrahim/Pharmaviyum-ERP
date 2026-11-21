"""Enforce semantic consistency between inventory movement types and deltas.

Revision ID: 2026_11_16_000002
Revises: 2026_11_16_000001
"""

from typing import Sequence, Union

from alembic import op


revision: str = "2026_11_16_000002"
down_revision: Union[str, None] = "2026_11_16_000001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_inventory_movements_type_delta_semantics",
        "inventory_movements",
        "("
        "movement_type IN ('goods_receipt', 'accepted_return', 'transfer_in', 'opening_balance') "
        "AND quantity_delta > 0 AND reserved_delta = 0"
        ") OR ("
        "movement_type IN ('cash_sale', 'write_off', 'expiry_disposal', 'transfer_out') "
        "AND quantity_delta < 0 AND reserved_delta = 0"
        ") OR ("
        "movement_type = 'payment_reservation' AND quantity_delta = 0 AND reserved_delta > 0"
        ") OR ("
        "movement_type = 'payment_settlement' AND quantity_delta < 0 "
        "AND reserved_delta = quantity_delta"
        ") OR ("
        "movement_type IN ('payment_failure', 'sale_cancellation') "
        "AND quantity_delta = 0 AND reserved_delta < 0"
        ") OR ("
        "movement_type = 'stock_adjustment' AND quantity_delta <> 0 AND reserved_delta = 0"
        ")",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_inventory_movements_type_delta_semantics",
        "inventory_movements",
        type_="check",
    )
