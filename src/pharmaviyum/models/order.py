from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from src.pharmaviyum.db.base import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id"), nullable=True, index=True)
    pharmacist_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    total_amount = Column(Float, default=0.0, nullable=False)
    status = Column(String(50), default="pending", nullable=False, index=True)
    payment_method = Column(String(20), nullable=True)
    payment_status = Column(String(20), default="unpaid", nullable=False)
    receipt_number = Column(String(64), unique=True, nullable=True, index=True)
    confirmed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    patient = relationship("Patient", backref="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
