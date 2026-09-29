"""POS cash shift lifecycle."""
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from src.pharmaviyum.db.base import Base

class CashShift(Base):
    __tablename__ = "cash_shifts"
    __table_args__ = (
        UniqueConstraint("pharmacy_id", "open_idempotency_key", name="uq_cash_shifts_open_idempotency"),
    )

    id = Column(Integer, primary_key=True, index=True)
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id", ondelete="RESTRICT"), nullable=False, index=True)
    pharmacist_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="open", index=True)
    opening_cash = Column(Float, nullable=False, default=0.0)
    closing_cash = Column(Float, nullable=True)
    expected_cash = Column(Float, nullable=True)
    difference = Column(Float, nullable=True)
    opened_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    open_idempotency_key = Column(String(255), nullable=True)
    close_idempotency_key = Column(String(255), nullable=True)
    close_reason = Column(String(500), nullable=True)
