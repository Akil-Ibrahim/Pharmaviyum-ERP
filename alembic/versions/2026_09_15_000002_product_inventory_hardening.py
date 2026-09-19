"""Harden product and inventory invariants.

Revision ID: 2026_09_15_000002
Revises: 20260915_pharmacy_domain
"""

from alembic import op
import sqlalchemy as sa

revision = "2026_09_15_000002"
down_revision = "20260915_pharmacy_domain"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # These constraints may already exist on databases deployed before
    # the pharmacy-domain migration was corrected. Keep this migration
    # idempotent for both fresh and partially migrated PostgreSQL databases.
    op.execute(
        """
        DO $
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'ck_products_price_nonnegative'
                  AND conrelid = 'products'::regclass
            ) THEN
                ALTER TABLE products
                ADD CONSTRAINT ck_products_price_nonnegative CHECK (price >= 0);
            END IF;
        END
        $;
        """
    )
    op.execute(
        """
        DO $
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'ck_products_stock_nonnegative'
                  AND conrelid = 'products'::regclass
            ) THEN
                ALTER TABLE products
                ADD CONSTRAINT ck_products_stock_nonnegative CHECK (stock >= 0);
            END IF;
        END
        $;
        """
    )
    op.add_column(
        "inventory",
        sa.Column("reorder_level", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_check_constraint(
        "ck_inventory_quantity_nonnegative", "inventory", "quantity >= 0"
    )
    op.create_check_constraint(
        "ck_inventory_reserved_nonnegative", "inventory", "reserved_quantity >= 0"
    )
    op.create_check_constraint(
        "ck_inventory_reserved_lte_quantity",
        "inventory",
        "reserved_quantity <= quantity",
    )
    op.create_check_constraint(
        "ck_inventory_reorder_level_nonnegative", "inventory", "reorder_level >= 0"
    )
    op.create_unique_constraint(
        "uq_inventory_product_pharmacy_lot",
        "inventory",
        ["product_id", "pharmacy_id", "lot_number"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_inventory_product_pharmacy_lot", "inventory", type_="unique")
    op.drop_constraint("ck_inventory_reorder_level_nonnegative", "inventory", type_="check")
    op.drop_constraint("ck_inventory_reserved_lte_quantity", "inventory", type_="check")
    op.drop_constraint("ck_inventory_reserved_nonnegative", "inventory", type_="check")
    op.drop_constraint("ck_inventory_quantity_nonnegative", "inventory", type_="check")
    op.drop_column("inventory", "reorder_level")
    op.execute(
        "ALTER TABLE products DROP CONSTRAINT IF EXISTS ck_products_stock_nonnegative"
    )
    op.execute(
        "ALTER TABLE products DROP CONSTRAINT IF EXISTS ck_products_price_nonnegative"
    )
