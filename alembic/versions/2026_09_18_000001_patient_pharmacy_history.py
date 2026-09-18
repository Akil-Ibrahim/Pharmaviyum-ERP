"""Add patient pharmacy categories and purchase history.

Revision ID: 2026_09_18_000001
Revises: 2026_09_16_000001
"""

from alembic import op
import sqlalchemy as sa


revision = "2026_09_18_000001"
down_revision = "2026_09_16_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "patients",
        sa.Column("customer_category", sa.String(length=50), nullable=False, server_default="General"),
    )
    op.create_index("ix_patients_customer_category", "patients", ["customer_category"])

    op.create_table(
        "patient_purchases",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("receipt_number", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Float(), nullable=False, server_default="0"),
        sa.Column("prescription_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("purchased_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_patient_purchases_patient_id", "patient_purchases", ["patient_id"])
    op.create_index("ix_patient_purchases_product_id", "patient_purchases", ["product_id"])
    op.create_index("ix_patient_purchases_receipt_number", "patient_purchases", ["receipt_number"])
    op.create_index("ix_patient_purchases_category", "patient_purchases", ["category"])
    op.create_index("ix_patient_purchases_purchased_at", "patient_purchases", ["purchased_at"])


def downgrade() -> None:
    op.drop_table("patient_purchases")
    op.drop_index("ix_patients_customer_category", table_name="patients")
    op.drop_column("patients", "customer_category")
