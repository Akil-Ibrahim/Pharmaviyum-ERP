from alembic import op
import sqlalchemy as sa

revision = "2026_09_15_000003"
down_revision = "2026_09_15_000002_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
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
