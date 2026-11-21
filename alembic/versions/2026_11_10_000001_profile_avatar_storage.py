"""Persist user profile photos in a dedicated PostgreSQL table."""

from alembic import op
import sqlalchemy as sa


revision = "2026_11_10_000001"
down_revision = "2026_11_05_000004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_avatars",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("avatar_data", sa.LargeBinary(), nullable=False),
        sa.Column("content_type", sa.String(length=50), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", name="pk_user_avatars"),
    )


def downgrade() -> None:
    op.drop_table("user_avatars")
