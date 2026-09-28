from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)

from src.pharmaviyum.db.base import Base


class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = (
        UniqueConstraint(
            "product_id", "pharmacy_id", "lot_number", name="uq_inventory_product_pharmacy_lot"
        ),
        CheckConstraint("quantity >= 0", name="ck_inventory_quantity_nonnegative"),
        CheckConstraint("reserved_quantity >= 0", name="ck_inventory_reserved_nonnegative"),
        CheckConstraint("reserved_quantity <= quantity", name="ck_inventory_reserved_lte_quantity"),
        CheckConstraint("reorder_level >= 0", name="ck_inventory_reorder_level_nonnegative"),
    )

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pharmacy_id = Column(
        Integer, ForeignKey("pharmacies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quantity = Column(Integer, nullable=False, default=0)
    reserved_quantity = Column(Integer, nullable=False, default=0)
    reorder_level = Column(Integer, nullable=False, default=0)
    batch_id = Column(Integer, ForeignKey("product_batches.id", ondelete="SET NULL"), nullable=True, index=True)
    lot_number = Column(String(100), nullable=True, index=True)
    expires_at = Column(DateTime, nullable=True, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
