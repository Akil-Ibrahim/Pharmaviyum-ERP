"""Purchase orders raised against suppliers."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from src.pharmaviyum.db.base import Base

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(64), unique=True, nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id", ondelete="RESTRICT"), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="draft", index=True)
    expected_delivery_at = Column(DateTime, nullable=True)
    currency = Column(String(3), nullable=False, default="USD")
    total_amount = Column(Float, nullable=False, default=0.0)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")
