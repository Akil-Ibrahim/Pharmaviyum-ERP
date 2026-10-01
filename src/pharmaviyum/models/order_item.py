from sqlalchemy import Column, Float, ForeignKey, Integer

from sqlalchemy.orm import relationship

from src.pharmaviyum.db.base import Base

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    batch_id = Column(Integer, ForeignKey("product_batches.id", ondelete="RESTRICT"), nullable=True, index=True)
    quantity_units = Column(Integer, nullable=False)
    dispensed_packs = Column(Integer, nullable=False, default=0)
    dispensed_blisters = Column(Integer, nullable=False, default=0)
    dispensed_units = Column(Integer, nullable=False, default=0)
    unit_price = Column(Float, nullable=False)
    line_total = Column(Float, nullable=False)
    order = relationship("Order", back_populates="items")
    product = relationship("Product")
    batch = relationship("ProductBatch")
