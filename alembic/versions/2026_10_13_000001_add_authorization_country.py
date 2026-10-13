"""Add authorisation country to medicinal products."""

from alembic import op
import sqlalchemy as sa

revision = "2026_10_13_000001"
down_revision = "2026_10_08_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "medicinal_products",
        sa.Column("authorization_country", sa.String(length=100), nullable=True),
    )
    op.create_index(
        "ix_medicinal_products_authorization_country",
        "medicinal_products",
        ["authorization_country"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_medicinal_products_authorization_country",
        table_name="medicinal_products",
    )
    op.drop_column("medicinal_products", "authorization_country")
