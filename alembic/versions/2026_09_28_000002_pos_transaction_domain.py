"""Add POS transaction domain: order lines, dispensing and inventory ledger.

Revision ID: 2026_09_28_000002
Revises: 2026_09_28_000001
"""

from alembic import op
import sqlalchemy as sa

revision = "2026_09_28_000002"
down_revision = "2026_09_28_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The legacy application has an Order model, but clean Alembic databases
    # do not have an orders migration. Bootstrap the canonical table before
    # extending it with the POS transaction fields below.
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("orders"):
        op.create_table(
            "orders",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("patient_id", sa.Integer(), nullable=False),
            sa.Column("total_amount", sa.Float(), nullable=False, server_default="0"),
            sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_orders_id", "orders", ["id"])
        op.create_index("ix_orders_patient_id", "orders", ["patient_id"])

    op.add_column("orders", sa.Column("pharmacy_id", sa.Integer(), nullable=True))
    op.add_column("orders", sa.Column("pharmacist_id", sa.Integer(), nullable=True))
    op.add_column("orders", sa.Column("payment_method", sa.String(length=20), nullable=True))
    op.add_column(
        "orders",
        sa.Column("payment_status", sa.String(length=20), nullable=False, server_default="unpaid"),
    )
    op.add_column("orders", sa.Column("receipt_number", sa.String(length=64), nullable=True))
    op.add_column("orders", sa.Column("confirmed_at", sa.DateTime(), nullable=True))
    op.create_index("ix_orders_pharmacy_id", "orders", ["pharmacy_id"])
    op.create_index("ix_orders_pharmacist_id", "orders", ["pharmacist_id"])
    op.create_index("ix_orders_status", "orders", ["status"])
    op.create_index("ix_orders_receipt_number", "orders", ["receipt_number"], unique=True)
    op.create_foreign_key("fk_orders_pharmacy_id", "orders", "pharmacies", ["pharmacy_id"], ["id"])
    op.create_foreign_key("fk_orders_pharmacist_id", "orders", "users", ["pharmacist_id"], ["id"])

    op.add_column("inventory", sa.Column("batch_id", sa.Integer(), nullable=True))
    op.create_index("ix_inventory_batch_id", "inventory", ["batch_id"])
    op.create_foreign_key("fk_inventory_batch_id", "inventory", "product_batches", ["batch_id"], ["id"])

    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=True),
        sa.Column("quantity_units", sa.Integer(), nullable=False),
        sa.Column("dispensed_packs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("dispensed_blisters", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("dispensed_units", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.Column("line_total", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["batch_id"], ["product_batches.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])
    op.create_index("ix_order_items_product_id", "order_items", ["product_id"])
    op.create_index("ix_order_items_batch_id", "order_items", ["batch_id"])

    op.create_table(
        "dispensings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pharmacy_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("prescription_id", sa.Integer(), nullable=True),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("inventory_id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=True),
        sa.Column("quantity_units", sa.Integer(), nullable=False),
        sa.Column("pharmacist_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="completed"),
        sa.Column("dispensed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["pharmacy_id"], ["pharmacies.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["prescription_id"], ["prescriptions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["inventory_id"], ["inventory.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["batch_id"], ["product_batches.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["pharmacist_id"], ["users.id"]),
    )
    for column in ("pharmacy_id", "patient_id", "order_id", "prescription_id", "product_id", "inventory_id", "batch_id", "pharmacist_id", "status", "dispensed_at"):
        op.create_index(f"ix_dispensings_{column}", "dispensings", [column])

    op.create_table(
        "inventory_transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pharmacy_id", sa.Integer(), nullable=False),
        sa.Column("inventory_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=True),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("dispensing_id", sa.Integer(), nullable=True),
        sa.Column("transaction_type", sa.String(length=32), nullable=False),
        sa.Column("quantity_delta", sa.Integer(), nullable=False),
        sa.Column("quantity_after", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["pharmacy_id"], ["pharmacies.id"]),
        sa.ForeignKeyConstraint(["inventory_id"], ["inventory.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["batch_id"], ["product_batches.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["dispensing_id"], ["dispensings.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
    )
    for column in ("pharmacy_id", "inventory_id", "product_id", "batch_id", "order_id", "dispensing_id", "transaction_type", "actor_id", "created_at"):
        op.create_index(f"ix_inventory_transactions_{column}", "inventory_transactions", [column])


def downgrade() -> None:
    for column in ("created_at", "actor_id", "transaction_type", "dispensing_id", "order_id", "batch_id", "product_id", "inventory_id", "pharmacy_id"):
        op.drop_index(f"ix_inventory_transactions_{column}", table_name="inventory_transactions")
    op.drop_table("inventory_transactions")
    for column in ("dispensed_at", "status", "pharmacist_id", "batch_id", "inventory_id", "product_id", "prescription_id", "order_id", "patient_id", "pharmacy_id"):
        op.drop_index(f"ix_dispensings_{column}", table_name="dispensings")
    op.drop_table("dispensings")
    op.drop_index("ix_order_items_batch_id", table_name="order_items")
    op.drop_index("ix_order_items_product_id", table_name="order_items")
    op.drop_index("ix_order_items_order_id", table_name="order_items")
    op.drop_table("order_items")
    op.drop_constraint("fk_inventory_batch_id", "inventory", type_="foreignkey")
    op.drop_index("ix_inventory_batch_id", table_name="inventory")
    op.drop_column("inventory", "batch_id")
    op.drop_constraint("fk_orders_pharmacist_id", "orders", type_="foreignkey")
    op.drop_constraint("fk_orders_pharmacy_id", "orders", type_="foreignkey")
    op.drop_index("ix_orders_receipt_number", table_name="orders")
    op.drop_index("ix_orders_status", table_name="orders")
    op.drop_index("ix_orders_pharmacist_id", table_name="orders")
    op.drop_index("ix_orders_pharmacy_id", table_name="orders")
    for column in ("confirmed_at", "receipt_number", "payment_status", "payment_method", "pharmacist_id", "pharmacy_id"):
        op.drop_column("orders", column)
