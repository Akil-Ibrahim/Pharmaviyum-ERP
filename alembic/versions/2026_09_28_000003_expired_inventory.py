"""Add separate accounting for expired pharmacy stock.

Revision ID: 2026_09_28_000003
Revises: 2026_09_28_000002
"""

from alembic import op
import sqlalchemy as sa

revision = "2026_09_28_000003"
down_revision = "2026_09_28_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "expired_inventory",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pharmacy_id", sa.Integer(), nullable=False),
        sa.Column("inventory_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=True),
        sa.Column("quantity_units", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=64), nullable=False, server_default="expired"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="quarantined"),
        sa.Column("quarantined_at", sa.DateTime(), nullable=False),
        sa.Column("disposed_at", sa.DateTime(), nullable=True),
        sa.Column("disposal_method", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["pharmacy_id"], ["pharmacies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["inventory_id"], ["inventory.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["batch_id"], ["product_batches.id"], ondelete="SET NULL"),
        sa.CheckConstraint("quantity_units > 0", name="ck_expired_inventory_quantity_positive"),
    )
    for column in ("pharmacy_id", "inventory_id", "product_id", "batch_id", "status", "quarantined_at"):
        op.create_index(f"ix_expired_inventory_{column}", "expired_inventory", [column])


def downgrade() -> None:
    for column in ("quarantined_at", "status", "batch_id", "product_id", "inventory_id", "pharmacy_id"):
        op.drop_index(f"ix_expired_inventory_{column}", table_name="expired_inventory")
    op.drop_table("expired_inventory")
