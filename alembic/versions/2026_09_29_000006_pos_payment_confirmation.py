"""Add POS payment confirmation timestamp.

Revision ID: 2026_09_29_000006
Revises: 2026_09_29_000005
"""

from alembic import op
import sqlalchemy as sa

revision = "2026_09_29_000006"
down_revision = "2026_09_29_000005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column("payment_confirmed_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_orders_payment_confirmed_at",
        "orders",
        ["payment_confirmed_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_orders_payment_confirmed_at", table_name="orders")
    op.drop_column("orders", "payment_confirmed_at")
