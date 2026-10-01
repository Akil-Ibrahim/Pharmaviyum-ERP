"""Received product batch and quantity details."""
from datetime import date

from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from src.pharmaviyum.db.base import Base


class GoodsReceiptItem(Base):
    __tablename__ = "goods_receipt_items"
    id = Column(Integer, primary_key=True, index=True)
    goods_receipt_id = Column(Integer, ForeignKey("goods_receipts.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    batch_id = Column(Integer, ForeignKey("product_batches.id", ondelete="RESTRICT"), nullable=True, index=True)
    batch_number = Column(String(64), nullable=False)
    expiry_date = Column(Date, nullable=False)
    quantity = Column(Integer, nullable=False)
    purchase_price = Column(Float, nullable=False, default=0.0)
    storage_location = Column(String(32), nullable=False, default="shelf")
    inspection_status = Column(String(32), nullable=False, default="accepted")
    rejection_reason = Column(String(500), nullable=True)
    receipt = relationship("GoodsReceipt", back_populates="items")
