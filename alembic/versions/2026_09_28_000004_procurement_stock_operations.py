"""Add procurement, receiving, transfers and temperature control domains.

Revision ID: 2026_09_28_000004
Revises: 2026_09_28_000003
"""
from alembic import op
import sqlalchemy as sa

revision = "2026_09_28_000004"
down_revision = "2026_09_28_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("storage_temperature_min", sa.Float(), nullable=True))
    op.add_column("products", sa.Column("storage_temperature_max", sa.Float(), nullable=True))
    op.add_column("products", sa.Column("storage_location_type", sa.String(length=32), nullable=False, server_default="shelf"))
    op.add_column("products", sa.Column("storage_instructions", sa.String(length=500), nullable=True))

    op.create_table(
        "supplier_products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("supplier_sku", sa.String(length=64), nullable=True),
        sa.Column("purchase_price", sa.Float(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("min_order_quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("lead_time_days", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("supplier_id", "product_id", name="uq_supplier_product"),
        sa.CheckConstraint("purchase_price >= 0", name="ck_supplier_products_price_nonnegative"),
        sa.CheckConstraint("min_order_quantity > 0", name="ck_supplier_products_min_order_positive"),
        sa.CheckConstraint("lead_time_days >= 0", name="ck_supplier_products_lead_time_nonnegative"),
    )
    op.create_index("ix_supplier_products_supplier_id", "supplier_products", ["supplier_id"])
    op.create_index("ix_supplier_products_product_id", "supplier_products", ["product_id"])
    op.create_index("ix_supplier_products_supplier_sku", "supplier_products", ["supplier_sku"])

    op.create_table(
        "defectura_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pharmacy_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=True),
        sa.Column("current_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reserved_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reorder_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("recommended_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["pharmacy_id"], ["pharmacies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="SET NULL"),
        sa.CheckConstraint("current_quantity >= 0", name="ck_defectura_current_nonnegative"),
        sa.CheckConstraint("reserved_quantity >= 0", name="ck_defectura_reserved_nonnegative"),
        sa.CheckConstraint("reorder_level >= 0", name="ck_defectura_reorder_nonnegative"),
        sa.CheckConstraint("recommended_quantity >= 0", name="ck_defectura_recommended_nonnegative"),
    )
    for column in ("pharmacy_id", "product_id", "supplier_id", "status"):
        op.create_index(f"ix_defectura_items_{column}", "defectura_items", [column])

    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_number", sa.String(length=64), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("pharmacy_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("expected_delivery_at", sa.DateTime(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("total_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["pharmacy_id"], ["pharmacies.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
        sa.UniqueConstraint("order_number"),
        sa.CheckConstraint("total_amount >= 0", name="ck_purchase_orders_total_nonnegative"),
    )
    for column in ("supplier_id", "pharmacy_id", "status", "created_by", "approved_by"):
        op.create_index(f"ix_purchase_orders_{column}", "purchase_orders", [column])
    op.create_index("ix_purchase_orders_order_number", "purchase_orders", ["order_number"])

    op.create_table(
        "purchase_order_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("purchase_order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("supplier_product_id", sa.Integer(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Float(), nullable=False, server_default="0"),
        sa.Column("line_total", sa.Float(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["supplier_product_id"], ["supplier_products.id"], ondelete="SET NULL"),
        sa.CheckConstraint("quantity > 0", name="ck_purchase_order_items_quantity_positive"),
        sa.CheckConstraint("unit_price >= 0", name="ck_purchase_order_items_unit_price_nonnegative"),
        sa.CheckConstraint("line_total >= 0", name="ck_purchase_order_items_line_total_nonnegative"),
    )
    for column in ("purchase_order_id", "product_id", "supplier_product_id"):
        op.create_index(f"ix_purchase_order_items_{column}", "purchase_order_items", [column])

    op.create_table(
        "goods_receipts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("receipt_number", sa.String(length=64), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=True),
        sa.Column("pharmacy_id", sa.Integer(), nullable=False),
        sa.Column("purchase_order_id", sa.Integer(), nullable=True),
        sa.Column("source_type", sa.String(length=32), nullable=False, server_default="supplier"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="accepted"),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.Column("received_by", sa.Integer(), nullable=False),
        sa.Column("notes", sa.String(length=1000), nullable=True),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["pharmacy_id"], ["pharmacies.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["received_by"], ["users.id"]),
        sa.UniqueConstraint("receipt_number"),
    )
    for column in ("supplier_id", "pharmacy_id", "purchase_order_id", "received_by"):
        op.create_index(f"ix_goods_receipts_{column}", "goods_receipts", [column])
    op.create_index("ix_goods_receipts_receipt_number", "goods_receipts", ["receipt_number"])

    op.create_table(
        "goods_receipt_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("goods_receipt_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=True),
        sa.Column("batch_number", sa.String(length=64), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("purchase_price", sa.Float(), nullable=False, server_default="0"),
        sa.Column("storage_location", sa.String(length=32), nullable=False, server_default="shelf"),
        sa.Column("inspection_status", sa.String(length=32), nullable=False, server_default="accepted"),
        sa.Column("rejection_reason", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["goods_receipt_id"], ["goods_receipts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["batch_id"], ["product_batches.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("quantity > 0", name="ck_goods_receipt_items_quantity_positive"),
        sa.CheckConstraint("purchase_price >= 0", name="ck_goods_receipt_items_price_nonnegative"),
    )
    for column in ("goods_receipt_id", "product_id", "batch_id", "inspection_status"):
        op.create_index(f"ix_goods_receipt_items_{column}", "goods_receipt_items", [column])

    op.create_table(
        "stock_transfers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("transfer_number", sa.String(length=64), nullable=False),
        sa.Column("source_pharmacy_id", sa.Integer(), nullable=False),
        sa.Column("destination_pharmacy_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("shipped_at", sa.DateTime(), nullable=True),
        sa.Column("received_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["source_pharmacy_id"], ["pharmacies.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["destination_pharmacy_id"], ["pharmacies.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
        sa.UniqueConstraint("transfer_number"),
    )
    for column in ("source_pharmacy_id", "destination_pharmacy_id", "status", "created_by", "approved_by"):
        op.create_index(f"ix_stock_transfers_{column}", "stock_transfers", [column])
    op.create_index("ix_stock_transfers_transfer_number", "stock_transfers", ["transfer_number"])

    op.create_table(
        "stock_transfer_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("stock_transfer_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["stock_transfer_id"], ["stock_transfers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["batch_id"], ["product_batches.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("quantity > 0", name="ck_stock_transfer_items_quantity_positive"),
    )
    for column in ("stock_transfer_id", "product_id", "batch_id"):
        op.create_index(f"ix_stock_transfer_items_{column}", "stock_transfer_items", [column])

    op.create_table(
        "temperature_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pharmacy_id", sa.Integer(), nullable=False),
        sa.Column("storage_location", sa.String(length=32), nullable=False),
        sa.Column("temperature_c", sa.Float(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.Column("recorded_by", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="within_range"),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["pharmacy_id"], ["pharmacies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recorded_by"], ["users.id"]),
    )
    for column in ("pharmacy_id", "storage_location", "recorded_at", "recorded_by", "status"):
        op.create_index(f"ix_temperature_logs_{column}", "temperature_logs", [column])


def downgrade() -> None:
    for column in ("pharmacy_id", "storage_location", "recorded_at", "recorded_by", "status"):
        op.drop_index(f"ix_temperature_logs_{column}", table_name="temperature_logs")
    op.drop_table("temperature_logs")
    for column in ("stock_transfer_items",):
        pass
    for column in ("stock_transfer_id", "product_id", "batch_id"):
        op.drop_index(f"ix_stock_transfer_items_{column}", table_name="stock_transfer_items")
    op.drop_table("stock_transfer_items")
    for column in ("transfer_number",):
        op.drop_index(f"ix_stock_transfers_{column}", table_name="stock_transfers")
    for column in ("source_pharmacy_id", "destination_pharmacy_id", "status", "created_by", "approved_by"):
        op.drop_index(f"ix_stock_transfers_{column}", table_name="stock_transfers")
    op.drop_table("stock_transfers")
    for column in ("goods_receipt_items",):
        pass
    for column in ("goods_receipt_id", "product_id", "batch_id", "inspection_status"):
        op.drop_index(f"ix_goods_receipt_items_{column}", table_name="goods_receipt_items")
    op.drop_table("goods_receipt_items")
    op.drop_index("ix_goods_receipts_receipt_number", table_name="goods_receipts")
    for column in ("supplier_id", "pharmacy_id", "purchase_order_id", "received_by"):
        op.drop_index(f"ix_goods_receipts_{column}", table_name="goods_receipts")
    op.drop_table("goods_receipts")
    for column in ("purchase_order_id", "product_id", "supplier_product_id"):
        op.drop_index(f"ix_purchase_order_items_{column}", table_name="purchase_order_items")
    op.drop_table("purchase_order_items")
    op.drop_index("ix_purchase_orders_order_number", table_name="purchase_orders")
    for column in ("supplier_id", "pharmacy_id", "status", "created_by", "approved_by"):
        op.drop_index(f"ix_purchase_orders_{column}", table_name="purchase_orders")
    op.drop_table("purchase_orders")
    for column in ("pharmacy_id", "product_id", "supplier_id", "status"):
        op.drop_index(f"ix_defectura_items_{column}", table_name="defectura_items")
    op.drop_table("defectura_items")
    for column in ("supplier_id", "product_id", "supplier_sku"):
        op.drop_index(f"ix_supplier_products_{column}", table_name="supplier_products")
    op.drop_table("supplier_products")
    for column in ("storage_instructions", "storage_location_type", "storage_temperature_max", "storage_temperature_min"):
        op.drop_column("products", column)
