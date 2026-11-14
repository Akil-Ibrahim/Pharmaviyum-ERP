"""Track manufacturer origin separately from authorization country."""

from alembic import op
import sqlalchemy as sa


revision = "2026_11_05_000003"
down_revision = "2026_11_05_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "medicinal_products",
        sa.Column("manufacturer_country", sa.String(length=100), nullable=True),
    )
    op.create_index(
        "ix_medicinal_products_manufacturer_country",
        "medicinal_products",
        ["manufacturer_country"],
    )
    op.add_column(
        "products",
        sa.Column("manufacturer_country", sa.String(length=100), nullable=True),
    )
    op.create_index(
        "ix_products_manufacturer_country",
        "products",
        ["manufacturer_country"],
    )


def downgrade() -> None:
    op.drop_index("ix_products_manufacturer_country", table_name="products")
    op.drop_column("products", "manufacturer_country")
    op.drop_index(
        "ix_medicinal_products_manufacturer_country",
        table_name="medicinal_products",
    )
    op.drop_column("medicinal_products", "manufacturer_country")
