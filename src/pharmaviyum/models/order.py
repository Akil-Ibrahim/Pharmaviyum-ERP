from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from src.pharmaviyum.db.base import Base


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint(
            "pharmacy_id",
            "idempotency_key",
            name="uq_orders_pharmacy_idempotency_key",
        ),
        UniqueConstraint(
            "pharmacy_id",
            "void_idempotency_key",
            name="uq_orders_pharmacy_void_idempotency_key",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id"), nullable=True, index=True)
    pharmacist_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    total_amount = Column(Float, default=0.0, nullable=False)
    status = Column(String(50), default="pending", nullable=False, index=True)
    payment_method = Column(String(20), nullable=True)
    payment_status = Column(String(20), default="unpaid", nullable=False)
    payment_confirmed_at = Column(DateTime, nullable=True)
    receipt_number = Column(String(64), unique=True, nullable=True, index=True)
    idempotency_key = Column(String(255), nullable=True)
    idempotency_request_hash = Column(String(64), nullable=True)
    void_idempotency_key = Column(String(255), nullable=True)
    voided_at = Column(DateTime, nullable=True)
    void_reason = Column(String(500), nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    patient = relationship("Patient", backref="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
