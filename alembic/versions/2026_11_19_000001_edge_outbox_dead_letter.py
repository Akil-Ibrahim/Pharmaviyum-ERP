"""Add durable Edge outbox dead-letter state and replay audit.

Revision ID: 2026_11_19_000001
Revises: 2026_11_16_000004
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_11_19_000001"
down_revision: Union[str, None] = "2026_11_16_000004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "outbox_events",
        sa.Column("dead_lettered_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "outbox_events",
        sa.Column("dead_letter_reason", sa.String(length=64), nullable=True),
    )
    op.create_check_constraint(
        "ck_outbox_events_dead_letter_state",
        "outbox_events",
        "(dead_lettered_at IS NULL AND dead_letter_reason IS NULL) OR "
        "(dead_lettered_at IS NOT NULL AND dead_letter_reason IS NOT NULL)",
    )
    op.create_index(
        "ix_outbox_events_dead_lettered",
        "outbox_events",
        ["dead_lettered_at", "created_at"],
    )
    op.create_table(
        "outbox_replay_audits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "outbox_event_id",
            sa.Integer(),
            sa.ForeignKey("outbox_events.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column(
            "actor_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("reason_code", sa.String(length=64), nullable=False),
        sa.Column(
            "previous_dead_letter_reason",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column("attempts_at_replay", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_outbox_replay_audits_event_created",
        "outbox_replay_audits",
        ["outbox_event_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_outbox_replay_audits_event_created",
        table_name="outbox_replay_audits",
    )
    op.drop_table("outbox_replay_audits")
    op.drop_index(
        "ix_outbox_events_dead_lettered",
        table_name="outbox_events",
    )
    op.drop_constraint(
        "ck_outbox_events_dead_letter_state",
        "outbox_events",
        type_="check",
    )
    op.drop_column("outbox_events", "dead_letter_reason")
    op.drop_column("outbox_events", "dead_lettered_at")
