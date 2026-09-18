"""Patient pharmacy purchase history entry."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.pharmaviyum.db.base import Base


class PatientPurchase(Base):
    __tablename__ = "patient_purchases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    batch_id: Mapped[int | None] = mapped_column(
        ForeignKey("product_batches.id", ondelete="SET NULL"), nullable=True, index=True
    )
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True
    )
    receipt_number: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    dispensed_packs: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    dispensed_blisters: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dispensed_units: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    prescription_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    purchased_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    patient = relationship("Patient", back_populates="purchases")
    product = relationship("Product")
    batch = relationship("ProductBatch")

    @property
    def product_name(self) -> str | None:
        return self.product.name if self.product is not None else None

    @property
    @property
    def batch_number(self) -> str | None:
        return self.batch.batch_number if self.batch is not None else None

    @property
    def expiry_date(self):
        return self.batch.expiry_date if self.batch is not None else None

    @property
    def total_amount(self) -> float:
        return round(self.quantity * self.unit_price, 2)
