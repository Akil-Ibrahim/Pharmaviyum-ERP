"""Add fencing tokens to transactional outbox leases."""

from alembic import op
import sqlalchemy as sa


revision = "2026_11_11_000003"
down_revision = "2026_11_11_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "outbox_events",
        sa.Column("lease_token", sa.String(length=36), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("outbox_events", "lease_token")
