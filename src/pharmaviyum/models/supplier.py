from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from src.pharmaviyum.db.base import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(64), unique=True, nullable=False, index=True)
    contact_name = Column(String(200), nullable=True)
    email = Column(String(320), nullable=True)
    phone = Column(String(32), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
