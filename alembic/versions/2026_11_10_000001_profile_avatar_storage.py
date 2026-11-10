"""Persist user profile photos in PostgreSQL."""

from alembic import op
import sqlalchemy as sa


revision = "2026_11_10_000001"
down_revision = "2026_11_05_000004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("avatar_data", sa.LargeBinary(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("avatar_content_type", sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "avatar_content_type")
    op.drop_column("users", "avatar_data")
