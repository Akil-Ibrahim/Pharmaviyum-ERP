"""Durable transactional outbox records for cross-site integration events."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.pharmaviyum.db.base import Base


class OutboxEvent(Base):
    """An immutable business event committed with its originating transaction."""

    __tablename__ = "outbox_events"
    __table_args__ = (
        UniqueConstraint("event_id", name="uq_outbox_events_event_id"),
        UniqueConstraint(
            "pharmacy_id",
            "aggregate_type",
            "aggregate_id",
            "aggregate_version",
            name="uq_outbox_events_aggregate_version",
        ),
        Index(
            "ix_outbox_events_pending",
            "published_at",
            "available_at",
            "created_at",
        ),
        Index("ix_outbox_events_pharmacy_created", "pharmacy_id", "created_at"),
        Index("ix_outbox_events_dead_lettered", "dead_lettered_at", "created_at"),
        CheckConstraint(
            "(dead_lettered_at IS NULL AND dead_letter_reason IS NULL) OR "
            "(dead_lettered_at IS NOT NULL AND dead_letter_reason IS NOT NULL)",
            name="ck_outbox_events_dead_letter_state",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(36), nullable=False)
    pharmacy_id: Mapped[int] = mapped_column(
        ForeignKey("pharmacies.id", ondelete="RESTRICT"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    aggregate_type: Mapped[str] = mapped_column(String(80), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(100), nullable=False)
    aggregate_version: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    dead_lettered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    dead_letter_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    lease_token: Mapped[str | None] = mapped_column(String(36), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(String(1000), nullable=True)


class OutboxReplayAudit(Base):
    """Durable audit record for an operator-authorized outbox replay."""

    __tablename__ = "outbox_replay_audits"
    __table_args__ = (
        Index("ix_outbox_replay_audits_event_created", "outbox_event_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    outbox_event_id: Mapped[int] = mapped_column(
        ForeignKey("outbox_events.id", ondelete="RESTRICT"), nullable=False
    )
    event_id: Mapped[str] = mapped_column(String(36), nullable=False)
    actor_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_dead_letter_reason: Mapped[str] = mapped_column(String(64), nullable=False)
    attempts_at_replay: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
