"""Create durable transactional outbox storage."""

from alembic import op
import sqlalchemy as sa


revision = "2026_11_11_000001"
down_revision = "2026_11_10_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "outbox_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("pharmacy_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("aggregate_type", sa.String(length=80), nullable=False),
        sa.Column("aggregate_id", sa.String(length=100), nullable=False),
        sa.Column("aggregate_version", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "available_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.String(length=1000), nullable=True),
        sa.ForeignKeyConstraint(
            ["pharmacy_id"], ["pharmacies.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("event_id", name="uq_outbox_events_event_id"),
        sa.UniqueConstraint(
            "pharmacy_id",
            "aggregate_type",
            "aggregate_id",
            "aggregate_version",
            name="uq_outbox_events_aggregate_version",
        ),
    )
    op.create_index(
        "ix_outbox_events_pending",
        "outbox_events",
        ["published_at", "available_at", "created_at"],
    )
    op.create_index(
        "ix_outbox_events_pharmacy_created",
        "outbox_events",
        ["pharmacy_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_outbox_events_pharmacy_created", table_name="outbox_events")
    op.drop_index("ix_outbox_events_pending", table_name="outbox_events")
    op.drop_table("outbox_events")
