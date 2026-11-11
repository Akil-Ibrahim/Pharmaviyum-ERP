"""Central synchronization identity and durable inbox persistence."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.pharmaviyum.db.base import Base


class PharmacyEdgeNode(Base):
    """A registered, individually revocable Pharmacy Edge installation."""

    __tablename__ = "pharmacy_edge_nodes"
    __table_args__ = (
        UniqueConstraint("node_id", name="uq_pharmacy_edge_nodes_node_id"),
        Index("ix_pharmacy_edge_nodes_pharmacy_active", "pharmacy_id", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    node_id: Mapped[str] = mapped_column(String(36), nullable=False)
    pharmacy_id: Mapped[int] = mapped_column(
        ForeignKey("pharmacies.id", ondelete="RESTRICT"), nullable=False
    )
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    credential_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class CentralInboxEvent(Base):
    """Durable receipt record; domain application is performed by a later consumer."""

    __tablename__ = "central_inbox_events"
    __table_args__ = (
        UniqueConstraint("event_id", name="uq_central_inbox_event_id"),
        UniqueConstraint(
            "pharmacy_id",
            "aggregate_type",
            "aggregate_id",
            "aggregate_version",
            name="uq_central_inbox_aggregate_version",
        ),
        Index("ix_central_inbox_pharmacy_received", "pharmacy_id", "received_at"),
        Index("ix_central_inbox_processing", "processing_status", "received_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(36), nullable=False)
    pharmacy_id: Mapped[int] = mapped_column(
        ForeignKey("pharmacies.id", ondelete="RESTRICT"), nullable=False
    )
    edge_node_id: Mapped[int] = mapped_column(
        ForeignKey("pharmacy_edge_nodes.id", ondelete="RESTRICT"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(80), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(100), nullable=False)
    aggregate_version: Mapped[int] = mapped_column(Integer, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    processing_status: Mapped[str] = mapped_column(
        String(24), nullable=False, default="accepted"
    )
    processing_error: Mapped[str | None] = mapped_column(String(1000), nullable=True)
