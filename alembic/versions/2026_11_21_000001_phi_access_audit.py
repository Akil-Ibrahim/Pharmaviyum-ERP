"""Create metadata-only PHI access audit records."""

from alembic import op
import sqlalchemy as sa


revision = "2026_11_21_000001"
down_revision = "2026_11_11_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "phi_access_audits",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("pharmacy_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("decision", sa.String(length=16), nullable=False),
        sa.Column("purpose", sa.String(length=48), nullable=False),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_phi_access_audits_actor_id", "phi_access_audits", ["actor_id"])
    op.create_index("ix_phi_access_audits_pharmacy_id", "phi_access_audits", ["pharmacy_id"])
    op.create_index("ix_phi_access_audits_patient_id", "phi_access_audits", ["patient_id"])


def downgrade() -> None:
    op.drop_index("ix_phi_access_audits_patient_id", table_name="phi_access_audits")
    op.drop_index("ix_phi_access_audits_pharmacy_id", table_name="phi_access_audits")
    op.drop_index("ix_phi_access_audits_actor_id", table_name="phi_access_audits")
    op.drop_table("phi_access_audits")
