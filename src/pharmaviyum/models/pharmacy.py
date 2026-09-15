from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from src.pharmaviyum.db.base import Base


class Pharmacy(Base):
    __tablename__ = "pharmacies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(64), unique=True, nullable=False, index=True)
    address = Column(String(500), nullable=True)
    timezone = Column(String(64), nullable=False, default="UTC")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
