"""Create per-pharmacy Edge identities and durable Central Inbox."""

from alembic import op
import sqlalchemy as sa


revision = "2026_11_11_000002"
down_revision = "2026_11_11_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pharmacy_edge_nodes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("node_id", sa.String(length=36), nullable=False),
        sa.Column("pharmacy_id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("credential_hash", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["pharmacy_id"], ["pharmacies.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("node_id", name="uq_pharmacy_edge_nodes_node_id"),
    )
    op.create_index(
        "ix_pharmacy_edge_nodes_pharmacy_active",
        "pharmacy_edge_nodes",
        ["pharmacy_id", "is_active"],
    )
    op.create_table(
        "central_inbox_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("pharmacy_id", sa.Integer(), nullable=False),
        sa.Column("edge_node_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("aggregate_type", sa.String(length=80), nullable=False),
        sa.Column("aggregate_id", sa.String(length=100), nullable=False),
        sa.Column("aggregate_version", sa.Integer(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "processing_status",
            sa.String(length=24),
            nullable=False,
            server_default="accepted",
        ),
        sa.Column("processing_error", sa.String(length=1000), nullable=True),
        sa.ForeignKeyConstraint(
            ["pharmacy_id"], ["pharmacies.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["edge_node_id"], ["pharmacy_edge_nodes.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("event_id", name="uq_central_inbox_event_id"),
        sa.UniqueConstraint(
            "pharmacy_id",
            "aggregate_type",
            "aggregate_id",
            "aggregate_version",
            name="uq_central_inbox_aggregate_version",
        ),
    )
    op.create_index(
        "ix_central_inbox_pharmacy_received",
        "central_inbox_events",
        ["pharmacy_id", "received_at"],
    )
    op.create_index(
        "ix_central_inbox_processing",
        "central_inbox_events",
        ["processing_status", "received_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_central_inbox_processing", table_name="central_inbox_events")
    op.drop_index(
        "ix_central_inbox_pharmacy_received", table_name="central_inbox_events"
    )
    op.drop_table("central_inbox_events")
    op.drop_index(
        "ix_pharmacy_edge_nodes_pharmacy_active", table_name="pharmacy_edge_nodes"
    )
    op.drop_table("pharmacy_edge_nodes")
