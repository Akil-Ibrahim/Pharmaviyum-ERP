from datetime import datetime

from sqlalchemy import (Boolean, CheckConstraint, Column, DateTime, Float,
                        Integer, String)

from src.pharmaviyum.db.base import Base


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_products_price_nonnegative"),
        CheckConstraint("stock >= 0", name="ck_products_stock_nonnegative"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    sku = Column(String(64), unique=True, index=True, nullable=False)
    description = Column(String(1000), nullable=True)
    price = Column(Float, nullable=False, default=0.0)
    # Legacy aggregate stock. Per-pharmacy stock is authoritative in Inventory.
    stock = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
