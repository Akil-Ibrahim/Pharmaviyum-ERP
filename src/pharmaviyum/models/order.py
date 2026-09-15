from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from src.pharmaviyum.db.base import Base


class Order(Base):
	__tablename__ = "orders"

	id = Column(Integer, primary_key=True, index=True)
	client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
	total_amount = Column(Float, default=0.0)
	status = Column(String(50), default="pending")
	created_at = Column(DateTime, default=datetime.utcnow)

	client = relationship("Client", backref="orders")
