"""Transactional point-of-sale sales, payment records, and lot allocations."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.pharmaviyum.db.base import Base

# Import referenced models so SQLAlchemy resolves all foreign keys during mapper setup.
from src.pharmaviyum.models.inventory import Inventory  # noqa: F401
from src.pharmaviyum.models.pharmacy import Pharmacy  # noqa: F401
from src.pharmaviyum.models.product import Product  # noqa: F401
from src.pharmaviyum.models.product_batch import ProductBatch  # noqa: F401
from src.pharmaviyum.models.user import User  # noqa: F401


class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = (
        UniqueConstraint("receipt_number", name="uq_sales_receipt_number"),
        UniqueConstraint(
            "pharmacy_id", "idempotency_key", name="uq_sales_pharmacy_idempotency"
        ),
        CheckConstraint(
            "subtotal >= 0 AND discount_total >= 0 AND total >= 0",
            name="ck_sales_amounts_nonnegative",
        ),
        CheckConstraint(
            "status IN ('awaiting_payment', 'completed', 'cancelled', 'refunded')",
            name="ck_sales_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    receipt_number: Mapped[str] = mapped_column(String(40), nullable=False)
    pharmacy_id: Mapped[int] = mapped_column(
        ForeignKey("pharmacies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    cashier_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    idempotency_key: Mapped[str] = mapped_column(String(100), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="UAH")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(24), nullable=False, default="awaiting_payment", index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    items: Mapped[list["SaleItem"]] = relationship(
        back_populates="sale", cascade="all, delete-orphan"
    )
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="sale", cascade="all, delete-orphan"
    )

    @property
    def cash_change(self) -> Decimal:
        return sum(
            (payment.change_due or Decimal("0.00") for payment in self.payments),
            Decimal("0.00"),
        )


class SaleItem(Base):
    __tablename__ = "sale_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_sale_items_quantity_positive"),
        CheckConstraint(
            "unit_price >= 0 AND line_total >= 0",
            name="ck_sale_items_amounts_nonnegative",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sale_id: Mapped[int] = mapped_column(
        ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    sale: Mapped[Sale] = relationship(back_populates="items")
    allocations: Mapped[list["SaleItemAllocation"]] = relationship(
        back_populates="sale_item", cascade="all, delete-orphan"
    )


class SaleItemAllocation(Base):
    __tablename__ = "sale_item_allocations"
    __table_args__ = (
        CheckConstraint(
            "quantity > 0", name="ck_sale_item_allocations_quantity_positive"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sale_item_id: Mapped[int] = mapped_column(
        ForeignKey("sale_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    inventory_id: Mapped[int] = mapped_column(
        ForeignKey("inventory.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    lot_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    sale_item: Mapped[SaleItem] = relationship(back_populates="allocations")


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
        CheckConstraint(
            "method IN ('cash', 'card_terminal', 'online')", name="ck_payments_method"
        ),
        CheckConstraint(
            "status IN ('pending', 'succeeded', 'failed', 'refunded')",
            name="ck_payments_status",
        ),
        UniqueConstraint(
            "provider_name",
            "provider_payment_id",
            name="uq_payments_provider_reference",
        ),
        UniqueConstraint(
            "sale_id", "idempotency_key", name="uq_payments_sale_idempotency"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sale_id: Mapped[int] = mapped_column(
        ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True
    )
    method: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cash_received: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    change_due: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="UAH")
    provider_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    provider_payment_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    settled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    sale: Mapped[Sale] = relationship(back_populates="payments")
