from alembic import op
import sqlalchemy as sa

revision = "2026_09_15_000004"
down_revision = "2026_09_15_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("role", sa.String(length=20), nullable=False, server_default="pharmacist"))


def downgrade() -> None:
    op.drop_column("users", "role")
