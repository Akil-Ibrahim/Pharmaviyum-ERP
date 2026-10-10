"""Create append-only inventory transaction ledger.

Revision ID: 2026_10_10_000002
Revises: 2026_10_10_000001
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "2026_10_10_000002"
down_revision: Union[str, None] = "2026_10_10_000001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if sa.inspect(bind).has_table("inventory_transactions"):
        return

    op.create_table(
        "inventory_transactions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("pharmacy_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("inventory_id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=True),
        sa.Column("transaction_type", sa.String(32), nullable=False),
        sa.Column("quantity_delta", sa.Integer(), nullable=False),
        sa.Column("reference_type", sa.String(32), nullable=False),
        sa.Column("reference_id", sa.Integer(), nullable=False),
        sa.Column("receipt_number", sa.String(64), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "quantity_delta <> 0",
            name="ck_inventory_transactions_nonzero_delta",
        ),
        sa.ForeignKeyConstraint(
            ["pharmacy_id"], ["pharmacies.id"], ondelete="CASCADE",
            name="fk_inventory_transactions_pharmacy_id",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"], ["products.id"], ondelete="RESTRICT",
            name="fk_inventory_transactions_product_id",
        ),
        sa.ForeignKeyConstraint(
            ["inventory_id"], ["inventory.id"], ondelete="RESTRICT",
            name="fk_inventory_transactions_inventory_id",
        ),
        sa.ForeignKeyConstraint(
            ["batch_id"], ["product_batches.id"], ondelete="SET NULL",
            name="fk_inventory_transactions_batch_id",
        ),
    )
    for column in (
        "pharmacy_id", "product_id", "inventory_id", "batch_id",
        "transaction_type", "reference_id", "receipt_number", "created_by",
        "created_at",
    ):
        op.create_index(
            f"ix_inventory_transactions_{column}",
            "inventory_transactions",
            [column],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("inventory_transactions"):
        return
    op.drop_table("inventory_transactions")
