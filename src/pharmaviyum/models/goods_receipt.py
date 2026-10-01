"""Goods receiving documents and their accounting status."""
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from src.pharmaviyum.db.base import Base

class GoodsReceipt(Base):
    __tablename__ = "goods_receipts"
    id = Column(Integer, primary_key=True, index=True)
    receipt_number = Column(String(64), unique=True, nullable=False, index=True)
    supplier_id = Column(ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=True, index=True)
    pharmacy_id = Column(ForeignKey("pharmacies.id", ondelete="RESTRICT"), nullable=False, index=True)
    purchase_order_id = Column(ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True, index=True)
    source_type = Column(String(32), nullable=False, default="supplier")
    status = Column(String(32), nullable=False, default="accepted")
    received_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    received_by = Column(ForeignKey("users.id"), nullable=False, index=True)
    notes = Column(String(1000), nullable=True)
    items = relationship("GoodsReceiptItem", back_populates="receipt", cascade="all, delete-orphan")
