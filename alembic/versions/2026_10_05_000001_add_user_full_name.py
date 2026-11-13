"""Add the canonical user full_name column.

The current User ORM model and auth CRUD expose full_name, while older
production databases may have the canonical users table without this column.
"""

from alembic import op
import sqlalchemy as sa

revision = "2026_10_05_000001"
down_revision = "2026_09_20_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("users"):
        return

    columns = {column["name"] for column in inspector.get_columns("users")}
    if "full_name" not in columns:
        op.add_column(
            "users",
            sa.Column("full_name", sa.String(length=200), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("users"):
        return

    columns = {column["name"] for column in inspector.get_columns("users")}
    if "full_name" in columns:
        op.drop_column("users", "full_name")
