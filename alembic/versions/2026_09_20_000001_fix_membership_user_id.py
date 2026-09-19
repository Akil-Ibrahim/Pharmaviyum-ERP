"""Align pharmacy membership foreign key with the canonical integer User model."""

from alembic import op
import sqlalchemy as sa

revision = "2026_09_20_000001"
down_revision = "2026_09_19_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("pharmacy_memberships"):
        return

    columns = {column["name"]: column for column in inspector.get_columns("pharmacy_memberships")}
    if "user_id" not in columns:
        return

    # UUID membership rows cannot be safely converted to the canonical integer
    # users.id without an explicit identity mapping. Fail closed rather than
    # silently corrupting tenant ownership.
    count = bind.execute(sa.text("SELECT count(*) FROM pharmacy_memberships")).scalar_one()
    if count:
        raise RuntimeError(
            "Cannot migrate pharmacy_memberships.user_id from UUID to integer while rows exist; "
            "export/map tenant memberships explicitly before deployment."
        )

    op.drop_constraint(
        "pharmacy_memberships_user_id_fkey",
        "pharmacy_memberships",
        type_="foreignkey",
    )
    op.alter_column(
        "pharmacy_memberships",
        "user_id",
        existing_type=sa.Uuid(),
        type_=sa.Integer(),
        existing_nullable=False,
        postgresql_using="user_id::text::integer",
    )
    op.create_foreign_key(
        "pharmacy_memberships_user_id_fkey",
        "pharmacy_memberships",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    raise RuntimeError("Downgrade intentionally blocked: tenant identity type changes require an explicit migration plan.")
