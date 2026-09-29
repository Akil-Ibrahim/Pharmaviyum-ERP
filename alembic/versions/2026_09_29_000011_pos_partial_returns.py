"""add POS partial returns

Revision ID: 2026_09_29_000011
Revises: 2026_09_29_000010
"""

from alembic import op
import sqlalchemy as sa


revision = "2026_09_29_000011"
down_revision = "2026_09_29_000010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pos_returns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pharmacy_id", sa.Integer(), sa.ForeignKey("pharmacies.id"), nullable=False),
        sa.Column(
            "order_id",
            sa.Integer(),
            sa.ForeignKey("orders.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column(
            "cash_shift_id",
            sa.Integer(),
            sa.ForeignKey("cash_shifts.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="completed"),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("refund_method", sa.String(length=20), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "pharmacy_id",
            "idempotency_key",
            name="uq_pos_returns_pharmacy_idempotency_key",
        ),
    )
    op.create_index("ix_pos_returns_id", "pos_returns", ["id"])
    op.create_index("ix_pos_returns_pharmacy_id", "pos_returns", ["pharmacy_id"])
    op.create_index("ix_pos_returns_order_id", "pos_returns", ["order_id"])
    op.create_index("ix_pos_returns_patient_id", "pos_returns", ["patient_id"])
    op.create_index("ix_pos_returns_cash_shift_id", "pos_returns", ["cash_shift_id"])
    op.create_index("ix_pos_returns_actor_id", "pos_returns", ["actor_id"])
    op.create_index("ix_pos_returns_status", "pos_returns", ["status"])
    op.create_table(
        "pos_return_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "return_id",
            sa.Integer(),
            sa.ForeignKey("pos_returns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "order_item_id",
            sa.Integer(),
            sa.ForeignKey("order_items.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("batch_id", sa.Integer(), sa.ForeignKey("product_batches.id"), nullable=True),
        sa.Column("quantity_units", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
    )
    op.create_index("ix_pos_return_items_id", "pos_return_items", ["id"])
    op.create_index("ix_pos_return_items_return_id", "pos_return_items", ["return_id"])
    op.create_index("ix_pos_return_items_order_item_id", "pos_return_items", ["order_item_id"])
    op.create_index("ix_pos_return_items_product_id", "pos_return_items", ["product_id"])
    op.create_index("ix_pos_return_items_batch_id", "pos_return_items", ["batch_id"])


def downgrade() -> None:
    op.drop_index("ix_pos_return_items_batch_id", table_name="pos_return_items")
    op.drop_index("ix_pos_return_items_product_id", table_name="pos_return_items")
    op.drop_index("ix_pos_return_items_order_item_id", table_name="pos_return_items")
    op.drop_index("ix_pos_return_items_return_id", table_name="pos_return_items")
    op.drop_index("ix_pos_return_items_id", table_name="pos_return_items")
    op.drop_table("pos_return_items")
    op.drop_index("ix_pos_returns_status", table_name="pos_returns")
    op.drop_index("ix_pos_returns_actor_id", table_name="pos_returns")
    op.drop_index("ix_pos_returns_cash_shift_id", table_name="pos_returns")
    op.drop_index("ix_pos_returns_patient_id", table_name="pos_returns")
    op.drop_index("ix_pos_returns_order_id", table_name="pos_returns")
    op.drop_index("ix_pos_returns_pharmacy_id", table_name="pos_returns")
    op.drop_index("ix_pos_returns_id", table_name="pos_returns")
    op.drop_table("pos_returns")
