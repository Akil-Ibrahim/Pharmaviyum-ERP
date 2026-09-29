from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from src.pharmaviyum.db.base import Base


class POSReturn(Base):
    __tablename__ = "pos_returns"
    __table_args__ = (
        UniqueConstraint(
            "pharmacy_id",
            "idempotency_key",
            name="uq_pos_returns_pharmacy_idempotency_key",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    cash_shift_id = Column(
        Integer, ForeignKey("cash_shifts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(30), default="completed", nullable=False, index=True)
    reason = Column(String(500), nullable=False)
    refund_method = Column(String(20), nullable=False)
    total_amount = Column(Float, default=0.0, nullable=False)
    idempotency_key = Column(String(255), nullable=False)
    request_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    items = relationship(
        "POSReturnItem", back_populates="return_record", cascade="all, delete-orphan"
    )


class POSReturnItem(Base):
    __tablename__ = "pos_return_items"

    id = Column(Integer, primary_key=True, index=True)
    return_id = Column(
        Integer, ForeignKey("pos_returns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_item_id = Column(
        Integer, ForeignKey("order_items.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    batch_id = Column(Integer, ForeignKey("product_batches.id"), nullable=True, index=True)
    quantity_units = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)

    return_record = relationship("POSReturn", back_populates="items")
