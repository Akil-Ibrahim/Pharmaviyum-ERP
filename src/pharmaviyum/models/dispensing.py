from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from src.pharmaviyum.db.base import Base


class Dispensing(Base):
    __tablename__ = "dispensings"
    id = Column(Integer, primary_key=True, index=True)
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id", ondelete="SET NULL"), nullable=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    inventory_id = Column(Integer, ForeignKey("inventory.id", ondelete="RESTRICT"), nullable=False, index=True)
    batch_id = Column(Integer, ForeignKey("product_batches.id", ondelete="RESTRICT"), nullable=True, index=True)
    quantity_units = Column(Integer, nullable=False)
    pharmacist_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="completed", index=True)
    dispensed_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    order = relationship("Order")
    patient = relationship("Patient")
    product = relationship("Product")
    inventory = relationship("Inventory")
    batch = relationship("ProductBatch")
