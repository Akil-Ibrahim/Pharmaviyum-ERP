from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from datetime import datetime
from src.pharmaviyum.db.base import Base


class User(Base):
	__tablename__ = "users"

	id = Column(Integer, primary_key=True, index=True)
	username = Column(String(100), unique=True, index=True, nullable=False)
	email = Column(String(200), nullable=True)
	hashed_password = Column(String(256), nullable=False)
	is_active = Column(Boolean, default=True)
	roles = Column(Text, nullable=True)
	created_at = Column(DateTime, default=datetime.utcnow)
	updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
