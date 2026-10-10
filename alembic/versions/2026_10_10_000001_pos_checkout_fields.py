"""Add POS receipt/payment fields and prescription flag.

Revision ID: 2026_10_10_000001
Revises: 2026_10_08_000002
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "2026_10_10_000001"
down_revision: Union[str, None] = "2026_10_08_000002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    order_columns = {c["name"] for c in sa.inspect(bind).get_columns("orders")}
    if "receipt_number" not in order_columns:
        op.add_column("orders", sa.Column("receipt_number", sa.String(64), nullable=True))
        op.create_index("ix_orders_receipt_number", "orders", ["receipt_number"], unique=True)
    if "payment_method" not in order_columns:
        op.add_column("orders", sa.Column("payment_method", sa.String(20), nullable=True))

    product_columns = {c["name"] for c in sa.inspect(bind).get_columns("products")}
    if "prescription_required" not in product_columns:
        op.add_column("products", sa.Column(
            "prescription_required", sa.Boolean(), nullable=False, server_default=sa.false()
        ))


def downgrade() -> None:
    bind = op.get_bind()
    product_columns = {c["name"] for c in sa.inspect(bind).get_columns("products")}
    if "prescription_required" in product_columns:
        op.drop_column("products", "prescription_required")
    order_columns = {c["name"] for c in sa.inspect(bind).get_columns("orders")}
    if "payment_method" in order_columns:
        op.drop_column("orders", "payment_method")
    if "receipt_number" in order_columns:
        op.drop_index("ix_orders_receipt_number", table_name="orders")
        op.drop_column("orders", "receipt_number")
