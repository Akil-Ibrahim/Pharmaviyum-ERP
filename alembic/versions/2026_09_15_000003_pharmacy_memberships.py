from alembic import op
import sqlalchemy as sa

revision = "2026_09_15_000003"
down_revision = "2026_09_15_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Fresh CI/test databases may not have the legacy users table because the
    # application model predates the current Alembic baseline. Create the
    # canonical integer-backed users table before adding its foreign key.
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("users"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("full_name", sa.String(length=200), nullable=True),
            sa.Column("username", sa.String(length=100), nullable=False),
            sa.Column("hashed_password", sa.String(length=255), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("email", name="uq_users_email"),
            sa.UniqueConstraint("username", name="uq_users_username"),
        )
        op.create_index("ix_users_id", "users", ["id"])
        op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "pharmacy_memberships",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("pharmacy_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["pharmacy_id"], ["pharmacies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "pharmacy_id", name="uq_pharmacy_membership_user_pharmacy"
        ),
    )
    op.create_index(
        "ix_pharmacy_memberships_user_id", "pharmacy_memberships", ["user_id"]
    )
    op.create_index(
        "ix_pharmacy_memberships_pharmacy_id", "pharmacy_memberships", ["pharmacy_id"]
    )


def downgrade() -> None:
    op.drop_index(
        "ix_pharmacy_memberships_pharmacy_id", table_name="pharmacy_memberships"
    )
    op.drop_index("ix_pharmacy_memberships_user_id", table_name="pharmacy_memberships")
    op.drop_table("pharmacy_memberships")
