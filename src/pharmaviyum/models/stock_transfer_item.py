"""Batch-aware stock transfer lines."""

from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from src.pharmaviyum.db.base import Base

class StockTransferItem(Base):
    __tablename__ = "stock_transfer_items"
    id = Column(Integer, primary_key=True, index=True)
    stock_transfer_id = Column(Integer, ForeignKey("stock_transfers.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    batch_id = Column(Integer, ForeignKey("product_batches.id", ondelete="RESTRICT"), nullable=True, index=True)
    quantity = Column(Integer, nullable=False)
    stock_transfer = relationship("StockTransfer", back_populates="items")
