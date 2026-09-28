"""Inter-location stock transfer documents."""
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from src.pharmaviyum.db.base import Base

class StockTransfer(Base):
    __tablename__ = "stock_transfers"
    id = Column(Integer, primary_key=True, index=True)
    transfer_number = Column(String(64), unique=True, nullable=False, index=True)
    source_pharmacy_id = Column(Integer, ForeignKey("pharmacies.id", ondelete="RESTRICT"), nullable=False, index=True)
    destination_pharmacy_id = Column(Integer, ForeignKey("pharmacies.id", ondelete="RESTRICT"), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="draft", index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    shipped_at = Column(DateTime, nullable=True)
    received_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    items = relationship("StockTransferItem", back_populates="transfer", cascade="all, delete-orphan")
