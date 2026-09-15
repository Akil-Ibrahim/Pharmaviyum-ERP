from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from src.pharmaviyum.db.base import Base


class MortariumAISession(Base):
    """Persist non-sensitive metadata for Mortarium AI interactions."""

    __tablename__ = "mortarium_ai_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    patient_id = Column(Integer, nullable=True, index=True)
    session_key = Column(String(128), unique=True, nullable=False, index=True)
    status = Column(String(32), nullable=False, default="active", index=True)
    last_activity_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
