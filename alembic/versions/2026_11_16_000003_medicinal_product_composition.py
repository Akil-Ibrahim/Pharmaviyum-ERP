"""Add normalized active-ingredient composition to medicinal products.

Revision ID: 2026_11_16_000003
Revises: 2026_11_16_000002
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_11_16_000003"
down_revision: Union[str, None] = "2026_11_16_000002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "medicinal_product_ingredients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "medicinal_product_id",
            sa.Integer(),
            sa.ForeignKey("medicinal_products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ingredient_name", sa.String(length=200), nullable=False),
        sa.Column("strength_value", sa.String(length=80), nullable=True),
        sa.Column("strength_unit", sa.String(length=40), nullable=True),
        sa.Column("source_identifier", sa.String(length=100), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "medicinal_product_id",
            "position",
            name="uq_medicinal_product_ingredient_position",
        ),
        sa.CheckConstraint(
            "position >= 0",
            name="ck_medicinal_product_ingredient_position",
        ),
    )
    op.create_index(
        "ix_medicinal_product_ingredients_medicinal_product_id",
        "medicinal_product_ingredients",
        ["medicinal_product_id"],
    )
    op.create_index(
        "ix_medicinal_product_ingredients_ingredient_name",
        "medicinal_product_ingredients",
        ["ingredient_name"],
    )

    # Preserve the current single-primary-ingredient relationship for existing
    # products. Component-level strengths remain unknown rather than inferred.
    op.execute(
        """
        INSERT INTO medicinal_product_ingredients
            (medicinal_product_id, ingredient_name, position)
        SELECT mp.id, dr.inn_name, 0
        FROM medicinal_products mp
        JOIN drug_references dr ON dr.id = mp.drug_reference_id
        """
    )


def downgrade() -> None:
    op.drop_index(
        "ix_medicinal_product_ingredients_ingredient_name",
        table_name="medicinal_product_ingredients",
    )
    op.drop_index(
        "ix_medicinal_product_ingredients_medicinal_product_id",
        table_name="medicinal_product_ingredients",
    )
    op.drop_table("medicinal_product_ingredients")
