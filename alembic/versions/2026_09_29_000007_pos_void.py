"""Add POS full-void fields and uniqueness.

Revision ID: 2026_09_29_000007
Revises: 2026_09_29_000006
"""

from alembic import op
import sqlalchemy as sa

revision = "2026_09_29_000007"
down_revision = "2026_09_29_000006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("void_idempotency_key", sa.String(length=255), nullable=True))
    op.add_column("orders", sa.Column("voided_at", sa.DateTime(), nullable=True))
    op.add_column("orders", sa.Column("void_reason", sa.String(length=500), nullable=True))
    op.create_index("ix_orders_void_idempotency_key", "orders", ["void_idempotency_key"])
    op.create_unique_constraint(
        "uq_orders_pharmacy_void_idempotency_key",
        "orders",
        ["pharmacy_id", "void_idempotency_key"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_orders_pharmacy_void_idempotency_key",
        "orders",
        type_="unique",
    )
    op.drop_index("ix_orders_void_idempotency_key", table_name="orders")
    op.drop_column("orders", "void_reason")
    op.drop_column("orders", "voided_at")
    op.drop_column("orders", "void_idempotency_key")
