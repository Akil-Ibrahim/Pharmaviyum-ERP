"""Add evidence-based halal assessment fields to products.

Revision ID: 2026_09_28_000001
Revises: 2026_09_15_000002
"""

from alembic import op
import sqlalchemy as sa

revision = "2026_09_28_000001"
down_revision = "2026_09_20_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column(
            "halal_status",
            sa.String(length=16),
            nullable=False,
            server_default="unknown",
        ),
    )
    op.add_column(
        "products",
        sa.Column("halal_standard", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("halal_evidence", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.create_check_constraint(
        "ck_products_halal_status",
        "products",
        "halal_status IN ('halal', 'haram', 'unknown')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_products_halal_status", "products", type_="check")
    op.drop_column("products", "halal_evidence")
    op.drop_column("products", "halal_standard")
    op.drop_column("products", "halal_status")
