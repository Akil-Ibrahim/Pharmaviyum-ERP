"""Create immutable POS payment transaction ledger.

Revision ID: 2026_09_29_000010
Revises: 2026_09_29_000009
"""
from alembic import op
import sqlalchemy as sa

revision = "2026_09_29_000010"
down_revision = "2026_09_29_000009"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "cash_transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cash_shift_id", sa.Integer(), sa.ForeignKey("cash_shifts.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("pharmacy_id", sa.Integer(), sa.ForeignKey("pharmacies.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("transaction_type", sa.String(length=32), nullable=False),
        sa.Column("payment_method", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("cash_shift_id", "idempotency_key", name="uq_cash_transactions_shift_idempotency"),
    )
    for name, column in [
        ("ix_cash_transactions_cash_shift_id", "cash_shift_id"),
        ("ix_cash_transactions_pharmacy_id", "pharmacy_id"),
        ("ix_cash_transactions_order_id", "order_id"),
        ("ix_cash_transactions_actor_id", "actor_id"),
        ("ix_cash_transactions_transaction_type", "transaction_type"),
        ("ix_cash_transactions_payment_method", "payment_method"),
        ("ix_cash_transactions_idempotency_key", "idempotency_key"),
        ("ix_cash_transactions_created_at", "created_at"),
    ]:
        op.create_index(name, "cash_transactions", [column])

def downgrade() -> None:
    op.drop_table("cash_transactions")
