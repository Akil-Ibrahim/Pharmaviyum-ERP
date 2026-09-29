"""Link POS orders to cash shifts.

Revision ID: 2026_09_29_000009
Revises: 2026_09_29_000008
"""
from alembic import op
import sqlalchemy as sa

revision = "2026_09_29_000009"
down_revision = "2026_09_29_000008"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("orders", sa.Column("cash_shift_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_orders_cash_shift_id",
        "orders",
        "cash_shifts",
        ["cash_shift_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_orders_cash_shift_id", "orders", ["cash_shift_id"])

def downgrade() -> None:
    op.drop_index("ix_orders_cash_shift_id", table_name="orders")
    op.drop_constraint("fk_orders_cash_shift_id", "orders", type_="foreignkey")
    op.drop_column("orders", "cash_shift_id")
