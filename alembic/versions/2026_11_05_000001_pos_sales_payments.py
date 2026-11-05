"""Create transactional POS sales, payments, and FEFO lot allocations."""

from alembic import op
import sqlalchemy as sa


revision = "2026_11_05_000001"
down_revision = ("2026_11_03_000001", "2026_10_13_000001")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sales",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("receipt_number", sa.String(40), nullable=False),
        sa.Column("pharmacy_id", sa.Integer(), nullable=False),
        sa.Column("cashier_user_id", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(100), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="UAH"),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column("discount_total", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="awaiting_payment"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["pharmacy_id"], ["pharmacies.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["cashier_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("receipt_number", name="uq_sales_receipt_number"),
        sa.UniqueConstraint("pharmacy_id", "idempotency_key", name="uq_sales_pharmacy_idempotency"),
        sa.CheckConstraint("subtotal >= 0 AND discount_total >= 0 AND total >= 0", name="ck_sales_amounts_nonnegative"),
        sa.CheckConstraint("status IN ('awaiting_payment', 'completed', 'cancelled', 'refunded')", name="ck_sales_status"),
    )
    op.create_index("ix_sales_receipt_number", "sales", ["receipt_number"])
    op.create_index("ix_sales_pharmacy_id", "sales", ["pharmacy_id"])
    op.create_index("ix_sales_cashier_user_id", "sales", ["cashier_user_id"])
    op.create_index("ix_sales_status", "sales", ["status"])

    op.create_table(
        "sale_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sale_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("product_name", sa.String(200), nullable=False),
        sa.Column("sku", sa.String(64), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("line_total", sa.Numeric(12, 2), nullable=False),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("quantity > 0", name="ck_sale_items_quantity_positive"),
        sa.CheckConstraint("unit_price >= 0 AND line_total >= 0", name="ck_sale_items_amounts_nonnegative"),
    )
    op.create_index("ix_sale_items_sale_id", "sale_items", ["sale_id"])
    op.create_index("ix_sale_items_product_id", "sale_items", ["product_id"])

    op.create_table(
        "sale_item_allocations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sale_item_id", sa.Integer(), nullable=False),
        sa.Column("inventory_id", sa.Integer(), nullable=False),
        sa.Column("lot_number", sa.String(100), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["sale_item_id"], ["sale_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["inventory_id"], ["inventory.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("quantity > 0", name="ck_sale_item_allocations_quantity_positive"),
    )
    op.create_index("ix_sale_item_allocations_sale_item_id", "sale_item_allocations", ["sale_item_id"])
    op.create_index("ix_sale_item_allocations_inventory_id", "sale_item_allocations", ["inventory_id"])

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sale_id", sa.Integer(), nullable=False),
        sa.Column("method", sa.String(24), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="UAH"),
        sa.Column("provider_name", sa.String(80), nullable=True),
        sa.Column("provider_payment_id", sa.String(160), nullable=True),
        sa.Column("idempotency_key", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("settled_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"], ondelete="CASCADE"),
        sa.CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
        sa.CheckConstraint("method IN ('cash', 'card_terminal', 'online')", name="ck_payments_method"),
        sa.CheckConstraint("status IN ('pending', 'succeeded', 'failed', 'refunded')", name="ck_payments_status"),
        sa.UniqueConstraint("provider_name", "provider_payment_id", name="uq_payments_provider_reference"),
        sa.UniqueConstraint("sale_id", "idempotency_key", name="uq_payments_sale_idempotency"),
    )
    op.create_index("ix_payments_sale_id", "payments", ["sale_id"])
    op.create_index("ix_payments_status", "payments", ["status"])


def downgrade() -> None:
    op.drop_index("ix_payments_status", table_name="payments")
    op.drop_index("ix_payments_sale_id", table_name="payments")
    op.drop_table("payments")
    op.drop_index("ix_sale_item_allocations_inventory_id", table_name="sale_item_allocations")
    op.drop_index("ix_sale_item_allocations_sale_item_id", table_name="sale_item_allocations")
    op.drop_table("sale_item_allocations")
    op.drop_index("ix_sale_items_product_id", table_name="sale_items")
    op.drop_index("ix_sale_items_sale_id", table_name="sale_items")
    op.drop_table("sale_items")
    op.drop_index("ix_sales_status", table_name="sales")
    op.drop_index("ix_sales_cashier_user_id", table_name="sales")
    op.drop_index("ix_sales_pharmacy_id", table_name="sales")
    op.drop_index("ix_sales_receipt_number", table_name="sales")
    op.drop_table("sales")
