"""Create POS cash shifts.

Revision ID: 2026_09_29_000008
Revises: 2026_09_29_000007
"""
from alembic import op
import sqlalchemy as sa

revision = "2026_09_29_000008"
down_revision = "2026_09_29_000007"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "cash_shifts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pharmacy_id", sa.Integer(), sa.ForeignKey("pharmacies.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("pharmacist_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("opening_cash", sa.Float(), nullable=False, server_default="0"),
        sa.Column("closing_cash", sa.Float(), nullable=True),
        sa.Column("expected_cash", sa.Float(), nullable=True),
        sa.Column("difference", sa.Float(), nullable=True),
        sa.Column("opened_at", sa.DateTime(), nullable=False),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("open_idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("close_idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("close_reason", sa.String(length=500), nullable=True),
        sa.UniqueConstraint("pharmacy_id", "open_idempotency_key", name="uq_cash_shifts_open_idempotency"),
    )
    op.create_index("ix_cash_shifts_pharmacy_id", "cash_shifts", ["pharmacy_id"])
    op.create_index("ix_cash_shifts_pharmacist_id", "cash_shifts", ["pharmacist_id"])
    op.create_index("ix_cash_shifts_status", "cash_shifts", ["status"])
    op.create_index("ix_cash_shifts_open_idempotency_key", "cash_shifts", ["open_idempotency_key"])

def downgrade() -> None:
    op.drop_table("cash_shifts")
