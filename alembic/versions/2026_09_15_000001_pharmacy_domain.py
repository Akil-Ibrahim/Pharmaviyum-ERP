"""Add pharmacy domain entities and ERP sync state.

Revision ID: 20260915_pharmacy_domain
Revises:
"""

from alembic import op
import sqlalchemy as sa


revision = "20260915_pharmacy_domain"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pharmacies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="UTC"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("code", name="uq_pharmacies_code"),
    )
    op.create_index("ix_pharmacies_id", "pharmacies", ["id"])
    op.create_index("ix_pharmacies_code", "pharmacies", ["code"])

    op.create_table(
        "suppliers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("contact_name", sa.String(200), nullable=True),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("code", name="uq_suppliers_code"),
    )
    op.create_index("ix_suppliers_id", "suppliers", ["id"])
    op.create_index("ix_suppliers_code", "suppliers", ["code"])

    op.create_table(
        "inventory",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("pharmacy_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reserved_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lot_number", sa.String(100), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["pharmacy_id"], ["pharmacies.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_inventory_id", "inventory", ["id"])
    op.create_index("ix_inventory_product_id", "inventory", ["product_id"])
    op.create_index("ix_inventory_pharmacy_id", "inventory", ["pharmacy_id"])
    op.create_index("ix_inventory_lot_number", "inventory", ["lot_number"])
    op.create_index("ix_inventory_expires_at", "inventory", ["expires_at"])

    op.create_table(
        "prescriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("prescription_number", sa.String(100), nullable=False),
        sa.Column("dosage", sa.String(200), nullable=True),
        sa.Column("instructions", sa.String(1000), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("issued_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("prescription_number", name="uq_prescriptions_number"),
    )
    op.create_index("ix_prescriptions_id", "prescriptions", ["id"])
    op.create_index("ix_prescriptions_patient_id", "prescriptions", ["patient_id"])
    op.create_index("ix_prescriptions_product_id", "prescriptions", ["product_id"])
    op.create_index("ix_prescriptions_status", "prescriptions", ["status"])
    op.create_index("ix_prescriptions_expires_at", "prescriptions", ["expires_at"])

    op.create_table(
        "erp_integrations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("provider", sa.String(100), nullable=False),
        sa.Column("endpoint", sa.String(500), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="disconnected"),
        sa.Column("sync_mode", sa.String(32), nullable=False, server_default="realtime"),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column("last_event_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_erp_integrations_id", "erp_integrations", ["id"])
    op.create_index("ix_erp_integrations_status", "erp_integrations", ["status"])

    op.create_table(
        "erp_sync_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("integration_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(128), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(128), nullable=True),
        sa.Column("direction", sa.String(16), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="received"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["integration_id"], ["erp_integrations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("event_id", name="uq_erp_sync_events_event_id"),
    )
    op.create_index("ix_erp_sync_events_id", "erp_sync_events", ["id"])
    op.create_index("ix_erp_sync_events_integration_id", "erp_sync_events", ["integration_id"])
    op.create_index("ix_erp_sync_events_entity_type", "erp_sync_events", ["entity_type"])
    op.create_index("ix_erp_sync_events_status", "erp_sync_events", ["status"])
    op.create_index("ix_erp_sync_events_received_at", "erp_sync_events", ["received_at"])

    op.create_table(
        "mortarium_ai_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=True),
        sa.Column("session_key", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("last_activity_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("session_key", name="uq_mortarium_ai_sessions_key"),
    )
    op.create_index("ix_mortarium_ai_sessions_id", "mortarium_ai_sessions", ["id"])
    op.create_index("ix_mortarium_ai_sessions_user_id", "mortarium_ai_sessions", ["user_id"])
    op.create_index("ix_mortarium_ai_sessions_patient_id", "mortarium_ai_sessions", ["patient_id"])
    op.create_index("ix_mortarium_ai_sessions_status", "mortarium_ai_sessions", ["status"])


def downgrade() -> None:
    op.drop_table("mortarium_ai_sessions")
    op.drop_table("erp_sync_events")
    op.drop_table("erp_integrations")
    op.drop_table("prescriptions")
    op.drop_table("inventory")
    op.drop_table("suppliers")
    op.drop_table("pharmacies")
