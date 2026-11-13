"""Add the canonical User.created_at column.

The User ORM expects users.created_at, while older production databases
may have the users table without this column. Backfill existing rows before
making the column non-nullable.
"""

from alembic import op
import sqlalchemy as sa

revision = "2026_10_05_000002"
down_revision = "2026_10_05_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("users"):
        return

    columns = {column["name"] for column in inspector.get_columns("users")}
    if "created_at" in columns:
        return

    op.add_column(
        "users",
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=True,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    bind.execute(
        sa.text(
            "UPDATE users SET created_at = CURRENT_TIMESTAMP "
            "WHERE created_at IS NULL"
        )
    )
    op.alter_column(
        "users",
        "created_at",
        existing_type=sa.DateTime(),
        nullable=False,
        server_default=None,
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("users"):
        return

    columns = {column["name"] for column in inspector.get_columns("users")}
    if "created_at" in columns:
        op.drop_column("users", "created_at")
