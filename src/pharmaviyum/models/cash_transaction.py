"""Immutable POS payment and cash movement ledger."""
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from src.pharmaviyum.db.base import Base

class CashTransaction(Base):
    __tablename__ = "cash_transactions"
    __table_args__ = (
        UniqueConstraint("cash_shift_id", "idempotency_key", name="uq_cash_transactions_shift_idempotency"),
    )

    id = Column(Integer, primary_key=True, index=True)
    cash_shift_id = Column(Integer, ForeignKey("cash_shifts.id", ondelete="RESTRICT"), nullable=False, index=True)
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id", ondelete="RESTRICT"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    transaction_type = Column(String(32), nullable=False, index=True)
    payment_method = Column(String(20), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    idempotency_key = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
