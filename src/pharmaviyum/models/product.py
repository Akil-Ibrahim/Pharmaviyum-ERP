from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from datetime import datetime
from src.pharmaviyum.db.base import Base


class Product(Base):
	__tablename__ = "products"

	id = Column(Integer, primary_key=True, index=True)
	name = Column(String(200), nullable=False)
	sku = Column(String(64), unique=True, index=True, nullable=False)
	description = Column(String(1000), nullable=True)
	price = Column(Float, nullable=False, default=0.0)
	stock = Column(Integer, default=0)
	is_active = Column(Boolean, default=True)
	created_at = Column(DateTime, default=datetime.utcnow)
	updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
