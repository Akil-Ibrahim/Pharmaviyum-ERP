from alembic import op
import sqlalchemy as sa

revision = "2026_09_15_000005"
down_revision = "2026_09_15_000004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("patients", sa.Column("pharmacy_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_patients_pharmacy_id",
        "patients",
        "pharmacies",
        ["pharmacy_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_patients_pharmacy_id", "patients", ["pharmacy_id"])


def downgrade() -> None:
    op.drop_index("ix_patients_pharmacy_id", table_name="patients")
    op.drop_constraint("fk_patients_pharmacy_id", "patients", type_="foreignkey")
    op.drop_column("patients", "pharmacy_id")
