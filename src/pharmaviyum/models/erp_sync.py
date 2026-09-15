from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)

from src.pharmaviyum.db.base import Base


class ERPIntegration(Base):
    __tablename__ = "erp_integrations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    provider = Column(String(100), nullable=False)
    endpoint = Column(String(500), nullable=False)
    status = Column(String(32), nullable=False, default="disconnected", index=True)
    sync_mode = Column(String(32), nullable=False, default="realtime")
    last_sync_at = Column(DateTime, nullable=True)
    last_event_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ERPSyncEvent(Base):
    __tablename__ = "erp_sync_events"

    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(
        Integer,
        ForeignKey("erp_integrations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_id = Column(String(128), unique=True, nullable=False, index=True)
    entity_type = Column(String(64), nullable=False, index=True)
    entity_id = Column(String(128), nullable=True)
    direction = Column(String(16), nullable=False)
    status = Column(String(32), nullable=False, default="received", index=True)
    error_message = Column(Text, nullable=True)
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    processed_at = Column(DateTime, nullable=True)
