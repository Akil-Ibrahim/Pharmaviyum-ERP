"""Create the append-only inventory movement journal.

Revision ID: 2026_11_16_000001
Revises: 2026_11_11_000003
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_11_16_000001"
down_revision: Union[str, None] = "2026_11_11_000003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "inventory_movements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "pharmacy_id",
            sa.Integer(),
            sa.ForeignKey("pharmacies.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "inventory_id",
            sa.Integer(),
            sa.ForeignKey("inventory.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.Integer(),
            sa.ForeignKey("products.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("movement_type", sa.String(32), nullable=False),
        sa.Column("quantity_delta", sa.Integer(), nullable=False),
        sa.Column("reserved_delta", sa.Integer(), nullable=False),
        sa.Column("quantity_before", sa.Integer(), nullable=False),
        sa.Column("quantity_after", sa.Integer(), nullable=False),
        sa.Column("reserved_before", sa.Integer(), nullable=False),
        sa.Column("reserved_after", sa.Integer(), nullable=False),
        sa.Column("actor_type", sa.String(16), nullable=False),
        sa.Column(
            "actor_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column("reference_type", sa.String(64), nullable=True),
        sa.Column("reference_id", sa.String(128), nullable=True),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("correlation_id", sa.String(128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "pharmacy_id",
            "idempotency_key",
            name="uq_inventory_movements_pharmacy_idempotency",
        ),
        sa.CheckConstraint(
            "movement_type IN ("
            "'goods_receipt', 'cash_sale', 'payment_reservation', "
            "'payment_settlement', 'payment_failure', 'sale_cancellation', "
            "'stock_adjustment', 'write_off', 'expiry_disposal', "
            "'accepted_return', 'transfer_in', 'transfer_out', 'opening_balance'"
            ")",
            name="ck_inventory_movements_type",
        ),
        sa.CheckConstraint(
            "actor_type IN ('user', 'system')",
            name="ck_inventory_movements_actor_type",
        ),
        sa.CheckConstraint(
            "(actor_type = 'user' AND actor_user_id IS NOT NULL) OR "
            "(actor_type = 'system' AND actor_user_id IS NULL)",
            name="ck_inventory_movements_actor_identity",
        ),
        sa.CheckConstraint(
            "quantity_before >= 0 AND quantity_after >= 0 "
            "AND reserved_before >= 0 AND reserved_after >= 0 "
            "AND reserved_before <= quantity_before "
            "AND reserved_after <= quantity_after",
            name="ck_inventory_movements_balances_nonnegative",
        ),
        sa.CheckConstraint(
            "quantity_after = quantity_before + quantity_delta "
            "AND reserved_after = reserved_before + reserved_delta",
            name="ck_inventory_movements_balance_deltas",
        ),
        sa.CheckConstraint(
            "quantity_delta <> 0 OR reserved_delta <> 0",
            name="ck_inventory_movements_nonzero_delta",
        ),
    )
    op.create_index(
        "ix_inventory_movements_inventory_created",
        "inventory_movements",
        ["inventory_id", "created_at"],
    )
    op.create_index(
        "ix_inventory_movements_pharmacy_created",
        "inventory_movements",
        ["pharmacy_id", "created_at"],
    )
    op.execute(
        """
        CREATE FUNCTION prevent_inventory_movement_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'inventory_movements is append-only';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_inventory_movements_append_only
        BEFORE UPDATE OR DELETE ON inventory_movements
        FOR EACH ROW EXECUTE FUNCTION prevent_inventory_movement_mutation()
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS trg_inventory_movements_append_only "
        "ON inventory_movements"
    )
    op.execute("DROP FUNCTION IF EXISTS prevent_inventory_movement_mutation()")
    op.drop_index(
        "ix_inventory_movements_pharmacy_created",
        table_name="inventory_movements",
    )
    op.drop_index(
        "ix_inventory_movements_inventory_created",
        table_name="inventory_movements",
    )
    op.drop_table("inventory_movements")
