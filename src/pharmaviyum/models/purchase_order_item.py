"""Lines in a supplier purchase order."""
from sqlalchemy import Column, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship
from src.pharmaviyum.db.base import Base

class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"
    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    supplier_product_id = Column(Integer, ForeignKey("supplier_products.id", ondelete="SET NULL"), nullable=True, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False, default=0.0)
    line_total = Column(Float, nullable=False, default=0.0)
    purchase_order = relationship("PurchaseOrder", back_populates="items")
