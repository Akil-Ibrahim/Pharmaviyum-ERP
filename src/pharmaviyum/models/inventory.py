from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.pharmaviyum.db.base import Base


class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "pharmacy_id",
            "lot_number",
            name="uq_inventory_product_pharmacy_lot",
        ),
        CheckConstraint("quantity >= 0", name="ck_inventory_quantity_nonnegative"),
        CheckConstraint(
            "reserved_quantity >= 0", name="ck_inventory_reserved_nonnegative"
        ),
        CheckConstraint(
            "reserved_quantity <= quantity", name="ck_inventory_reserved_lte_quantity"
        ),
        CheckConstraint(
            "reorder_level >= 0", name="ck_inventory_reorder_level_nonnegative"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pharmacy_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("pharmacies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reserved_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reorder_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lot_number: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
