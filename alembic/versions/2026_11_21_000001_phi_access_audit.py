"""Create metadata-only PHI access audit records."""

from alembic import op
import sqlalchemy as sa

revision = "2026_11_21_000001"
down_revision = "2026_11_16_000001"
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
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_phi_access_audits_actor_id", "phi_access_audits", ["actor_id"])
    op.create_index("ix_phi_access_audits_pharmacy_id", "phi_access_audits", ["pharmacy_id"])
    op.create_index("ix_phi_access_audits_patient_id", "phi_access_audits", ["patient_id"])
    op.create_index("ix_patient_purchases_patient_purchased_at_id", "patient_purchases", ["patient_id", "purchased_at", "id"])
    op.execute("""
        CREATE FUNCTION reject_phi_access_audit_mutation() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'phi_access_audits is append-only';
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER trg_phi_access_audits_append_only
        BEFORE UPDATE OR DELETE ON phi_access_audits
        FOR EACH ROW EXECUTE FUNCTION reject_phi_access_audit_mutation()
    """)

def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_phi_access_audits_append_only ON phi_access_audits")
    op.execute("DROP FUNCTION IF EXISTS reject_phi_access_audit_mutation()")
    op.drop_index("ix_patient_purchases_patient_purchased_at_id", table_name="patient_purchases")
    op.drop_index("ix_phi_access_audits_patient_id", table_name="phi_access_audits")
    op.drop_index("ix_phi_access_audits_pharmacy_id", table_name="phi_access_audits")
    op.drop_index("ix_phi_access_audits_actor_id", table_name="phi_access_audits")
    op.drop_table("phi_access_audits")