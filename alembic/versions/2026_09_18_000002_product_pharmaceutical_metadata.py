"""Add pharmaceutical package, barcode and batch/expiry metadata."""

from alembic import op
import sqlalchemy as sa


revision = "2026_09_18_000002"
down_revision = "2026_09_18_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = [
        ("dosage_strength", sa.String(length=100)),
        ("dosage_form", sa.String(length=50)),
        ("units_per_pack", sa.Integer(), False),
        ("package_type", sa.String(length=50), False),
        ("blisters_per_pack", sa.Integer(), False),
        ("units_per_blister", sa.Integer(), False),
        ("manufacturer", sa.String(length=200)),
        ("inn_name", sa.String(length=200)),
        ("atc_code", sa.String(length=20)),
        ("regulatory_id", sa.String(length=50)),
        ("gtin", sa.String(length=14)),
        ("barcode", sa.String(length=64)),
    ]
    for item in columns:
        name, typ, *rest = item
        nullable = rest[0] if rest else True
        op.add_column(
            "products",
            sa.Column(
                name,
                typ,
                nullable=nullable,
                server_default=("1" if name == "units_per_pack" else "pack" if name == "package_type" else "0" if name in {"blisters_per_pack", "units_per_blister"} else None),
            ),
        )

    op.create_index("ix_products_inn_name", "products", ["inn_name"])
    op.create_index("ix_products_atc_code", "products", ["atc_code"])
    op.create_index("ix_products_gtin", "products", ["gtin"])
    op.create_index("ix_products_barcode", "products", ["barcode"])

    op.create_table(
        "product_batches",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("batch_number", sa.String(length=64), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=False),
        sa.Column("received_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("barcode", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_product_batches_product_id", "product_batches", ["product_id"])
    op.create_index("ix_product_batches_batch_number", "product_batches", ["batch_number"])
    op.create_index("ix_product_batches_expiry_date", "product_batches", ["expiry_date"])
    op.create_index("ix_product_batches_barcode", "product_batches", ["barcode"])

    op.add_column("patient_purchases", sa.Column("batch_id", sa.Integer(), nullable=True))
    op.add_column("patient_purchases", sa.Column("dispensed_packs", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("patient_purchases", sa.Column("dispensed_blisters", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("patient_purchases", sa.Column("dispensed_units", sa.Integer(), nullable=False, server_default="0"))
    op.create_foreign_key(
        "fk_patient_purchases_batch_id",
        "patient_purchases",
        "product_batches",
        ["batch_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_patient_purchases_batch_id", "patient_purchases", ["batch_id"])


def downgrade() -> None:
    op.drop_index("ix_patient_purchases_batch_id", table_name="patient_purchases")
    op.drop_constraint("fk_patient_purchases_batch_id", "patient_purchases", type_="foreignkey")
    op.drop_column("patient_purchases", "dispensed_units")
    op.drop_column("patient_purchases", "dispensed_blisters")
    op.drop_column("patient_purchases", "dispensed_packs")
    op.drop_column("patient_purchases", "batch_id")
    op.drop_table("product_batches")
    for name in ["barcode", "gtin", "atc_code", "inn_name"]:
        op.drop_index(f"ix_products_{name}", table_name="products")
    for name in [
        "dosage_strength",
        "dosage_form",
        "units_per_pack",
        "package_type",
        "blisters_per_pack",
        "units_per_blister",
        "manufacturer",
        "inn_name",
        "atc_code",
        "regulatory_id",
        "gtin",
        "barcode",
    ]:
        op.drop_column("products", name)
