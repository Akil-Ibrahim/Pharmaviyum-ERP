"""Recorded temperature observations for pharmacy storage areas."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String

from src.pharmaviyum.db.base import Base

class TemperatureLog(Base):
    __tablename__ = "temperature_logs"
    id = Column(Integer, primary_key=True, index=True)
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id", ondelete="CASCADE"), nullable=False, index=True)
    storage_location = Column(String(32), nullable=False)
    temperature_c = Column(Float, nullable=False)
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="within_range")
    notes = Column(String(500), nullable=True)
