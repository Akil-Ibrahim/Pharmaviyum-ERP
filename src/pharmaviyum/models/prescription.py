from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from src.pharmaviyum.db.base import Base


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=True, index=True)
    prescription_number = Column(String(100), unique=True, nullable=False, index=True)
    dosage = Column(String(200), nullable=True)
    instructions = Column(String(1000), nullable=True)
    status = Column(String(32), nullable=False, default="active", index=True)
    issued_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
