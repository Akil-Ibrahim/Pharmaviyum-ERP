from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.pharmaviyum.db.base import Base
from src.pharmaviyum.models.drug_catalog import MedicinalProduct

if False:  # pragma: no cover
    from src.pharmaviyum.models.product_batch import ProductBatch


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_products_price_nonnegative"),
        CheckConstraint("stock >= 0", name="ck_products_stock_nonnegative"),
        CheckConstraint(
            "units_per_pack > 0", name="ck_products_units_per_pack_positive"
        ),
        CheckConstraint(
            "units_per_blister >= 0",
            name="ck_products_units_per_blister_nonnegative",
        ),
        CheckConstraint(
            "blisters_per_pack >= 0",
            name="ck_products_blisters_per_pack_nonnegative",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    dosage_strength: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dosage_form: Mapped[str | None] = mapped_column(String(50), nullable=True)
    units_per_pack: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    package_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pack"
    )
    blisters_per_pack: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    units_per_blister: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    manufacturer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    inn_name: Mapped[str | None] = mapped_column(
        String(200), nullable=True, index=True
    )
    atc_code: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    regulatory_id: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True
    )
    gtin: Mapped[str | None] = mapped_column(String(14), nullable=True, index=True)
    barcode: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    medicinal_product_id: Mapped[int | None] = mapped_column(
        ForeignKey("medicinal_products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    medicinal_product: Mapped[MedicinalProduct | None] = relationship()

    price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    batches: Mapped[list["ProductBatch"]] = relationship(
        "ProductBatch", back_populates="product", cascade="all, delete-orphan"
    )
