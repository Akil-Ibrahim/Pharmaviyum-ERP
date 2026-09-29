"""Add international drug reference and medicinal product catalog."""

from alembic import op
import sqlalchemy as sa


revision = "2026_09_29_000001"
down_revision = "2026_09_20_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "drug_references",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("inn_name", sa.String(length=200), nullable=False),
        sa.Column("atc_code", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_drug_references_inn_name", "drug_references", ["inn_name"])
    op.create_index("ix_drug_references_atc_code", "drug_references", ["atc_code"])

    op.create_table(
        "drug_reference_ingredients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("drug_reference_id", sa.Integer(), nullable=False),
        sa.Column("ingredient_name", sa.String(length=200), nullable=False),
        sa.ForeignKeyConstraint(
            ["drug_reference_id"], ["drug_references.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_drug_reference_ingredients_drug_reference_id",
        "drug_reference_ingredients",
        ["drug_reference_id"],
    )
    op.create_index(
        "ix_drug_reference_ingredients_ingredient_name",
        "drug_reference_ingredients",
        ["ingredient_name"],
    )

    op.create_table(
        "medicinal_products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("drug_reference_id", sa.Integer(), nullable=False),
        sa.Column("brand_name", sa.String(length=200), nullable=True),
        sa.Column("product_type", sa.String(length=30), nullable=False, server_default="generic"),
        sa.Column("manufacturer", sa.String(length=200), nullable=True),
        sa.Column("strength", sa.String(length=100), nullable=True),
        sa.Column("dosage_form", sa.String(length=100), nullable=True),
        sa.Column("route", sa.String(length=100), nullable=True),
        sa.Column("package_description", sa.String(length=200), nullable=True),
        sa.Column("gtin", sa.String(length=14), nullable=True),
        sa.Column("regulatory_id", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["drug_reference_id"], ["drug_references.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_medicinal_products_drug_reference_id",
        "medicinal_products",
        ["drug_reference_id"],
    )
    op.create_index("ix_medicinal_products_brand_name", "medicinal_products", ["brand_name"])
    op.create_index(
        "ix_medicinal_products_manufacturer", "medicinal_products", ["manufacturer"]
    )
    op.create_index("ix_medicinal_products_gtin", "medicinal_products", ["gtin"])
    op.create_index(
        "ix_medicinal_products_regulatory_id",
        "medicinal_products",
        ["regulatory_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_medicinal_products_regulatory_id", table_name="medicinal_products")
    op.drop_index("ix_medicinal_products_gtin", table_name="medicinal_products")
    op.drop_index("ix_medicinal_products_manufacturer", table_name="medicinal_products")
    op.drop_index("ix_medicinal_products_brand_name", table_name="medicinal_products")
    op.drop_index(
        "ix_medicinal_products_drug_reference_id", table_name="medicinal_products"
    )
    op.drop_table("medicinal_products")

    op.drop_index(
        "ix_drug_reference_ingredients_ingredient_name",
        table_name="drug_reference_ingredients",
    )
    op.drop_index(
        "ix_drug_reference_ingredients_drug_reference_id",
        table_name="drug_reference_ingredients",
    )
    op.drop_table("drug_reference_ingredients")

    op.drop_index("ix_drug_references_atc_code", table_name="drug_references")
    op.drop_index("ix_drug_references_inn_name", table_name="drug_references")
    op.drop_table("drug_references")
