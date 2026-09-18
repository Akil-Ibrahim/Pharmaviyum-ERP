from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from src.pharmaviyum.db.base import Base


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_products_price_nonnegative"),
        CheckConstraint("stock >= 0", name="ck_products_stock_nonnegative"),
        CheckConstraint("units_per_pack > 0", name="ck_products_units_per_pack_positive"),
        CheckConstraint("units_per_blister >= 0", name="ck_products_units_per_blister_nonnegative"),
        CheckConstraint("blisters_per_pack >= 0", name="ck_products_blisters_per_pack_nonnegative"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    sku = Column(String(64), unique=True, index=True, nullable=False)
    description = Column(String(1000), nullable=True)
    dosage_strength = Column(String(100), nullable=True)
    dosage_form = Column(String(50), nullable=True)
    units_per_pack = Column(Integer, nullable=False, default=1)
    package_type = Column(String(50), nullable=False, default="pack")
    blisters_per_pack = Column(Integer, nullable=False, default=0)
    units_per_blister = Column(Integer, nullable=False, default=0)
    manufacturer = Column(String(200), nullable=True)
    inn_name = Column(String(200), nullable=True, index=True)
    atc_code = Column(String(20), nullable=True, index=True)
    regulatory_id = Column(String(50), nullable=True, index=True)
    gtin = Column(String(14), nullable=True, index=True)
    barcode = Column(String(64), nullable=True, index=True)

    price = Column(Float, nullable=False, default=0.0)
    # Legacy aggregate stock. Per-pharmacy stock is authoritative in Inventory.
    stock = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    batches = relationship(
        "ProductBatch", back_populates="product", cascade="all, delete-orphan"
    )
