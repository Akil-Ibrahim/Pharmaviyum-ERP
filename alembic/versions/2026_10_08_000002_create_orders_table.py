"""Create the orders table required by order and dashboard APIs.

Revision ID: 2026_10_08_000002
Revises: 2026_10_08_000001
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_10_08_000002"
down_revision: Union[str, None] = "2026_10_08_000001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(bind: sa.Connection, name: str) -> bool:
    return sa.inspect(bind).has_table(name)


def upgrade() -> None:
    bind = op.get_bind()

    if _table_exists(bind, "orders"):
        return

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], name="orders_patient_id_fkey"),
    )
    op.create_index("ix_orders_patient_id", "orders", ["patient_id"])
    op.create_index("ix_orders_status", "orders", ["status"])
    op.create_index("ix_orders_created_at", "orders", ["created_at"])


def downgrade() -> None:
    bind = op.get_bind()
    if _table_exists(bind, "orders"):
        op.drop_index("ix_orders_created_at", table_name="orders")
        op.drop_index("ix_orders_status", table_name="orders")
        op.drop_index("ix_orders_patient_id", table_name="orders")
        op.drop_table("orders")
