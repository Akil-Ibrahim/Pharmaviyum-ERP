"""Separate accounting for stock quarantined because it has expired."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.pharmaviyum.db.base import Base


class ExpiredInventory(Base):
    __tablename__ = "expired_inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pharmacy_id: Mapped[int] = mapped_column(
        ForeignKey("pharmacies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    inventory_id: Mapped[int] = mapped_column(
        ForeignKey("inventory.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    batch_id: Mapped[int | None] = mapped_column(
        ForeignKey("product_batches.id", ondelete="SET NULL"), nullable=True, index=True
    )
    quantity_units: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(64), nullable=False, default="expired")
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="quarantined", index=True
    )
    quarantined_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, index=True
    )
    disposed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    disposal_method: Mapped[str | None] = mapped_column(String(100), nullable=True)

    pharmacy = relationship("Pharmacy")
    inventory = relationship("Inventory")
    product = relationship("Product")
    batch = relationship("ProductBatch")

