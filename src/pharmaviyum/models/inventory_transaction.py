from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from src.pharmaviyum.db.base import Base

class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"
    id = Column(Integer, primary_key=True, index=True)
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id"), nullable=False, index=True)
    inventory_id = Column(Integer, ForeignKey("inventory.id", ondelete="RESTRICT"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    batch_id = Column(Integer, ForeignKey("product_batches.id", ondelete="RESTRICT"), nullable=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    dispensing_id = Column(Integer, ForeignKey("dispensings.id", ondelete="SET NULL"), nullable=True, index=True)
    transaction_type = Column(String(32), nullable=False, index=True)
    quantity_delta = Column(Integer, nullable=False)
    quantity_after = Column(Integer, nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
