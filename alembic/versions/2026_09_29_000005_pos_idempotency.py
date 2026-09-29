"""Add database-backed POS transaction idempotency.

Revision ID: 2026_09_29_000005
Revises: 2026_09_28_000004
"""

from alembic import op
import sqlalchemy as sa

revision = "2026_09_29_000005"
down_revision = "2026_09_28_000004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("idempotency_key", sa.String(length=255), nullable=True))
    op.add_column("orders", sa.Column("idempotency_request_hash", sa.String(length=64), nullable=True))
    op.create_index(
        "ix_orders_idempotency_key",
        "orders",
        ["idempotency_key"],
    )
    op.create_unique_constraint(
        "uq_orders_pharmacy_idempotency_key",
        "orders",
        ["pharmacy_id", "idempotency_key"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_orders_pharmacy_idempotency_key",
        "orders",
        type_="unique",
    )
    op.drop_index("ix_orders_idempotency_key", table_name="orders")
    op.drop_column("orders", "idempotency_request_hash")
    op.drop_column("orders", "idempotency_key")
