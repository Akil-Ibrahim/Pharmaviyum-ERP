# models/client.py - Customer/Client ORM model for pharmacy CRM
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

from src.pharmaviyum.db.base import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(200), nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    email = Column(String(100), nullable=True)
    birth_date = Column(DateTime, nullable=True)

    # Pharmacy specific fields
    discount_card = Column(String(50), unique=True, nullable=True)
    discount_percent = Column(Float, default=0.0)
    is_privileged = Column(Boolean, default=False)
    privilege_type = Column(String(100), nullable=True)

    # Medical context for RAG
    chronic_diseases = Column(Text, nullable=True)
    allergies = Column(Text, nullable=True)
    regular_medications = Column(Text, nullable=True)

    address = Column(String(300), nullable=True)

    # Status & activity
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_visit = Column(DateTime, nullable=True)

    # Aggregated purchase data
    total_purchases = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
