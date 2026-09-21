"""Patient condition entity."""

from datetime import datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.pharmaviyum.db.base import Base

if False:  # pragma: no cover
    from src.pharmaviyum.models.patients.patient import Patient


class PatientCondition(Base):
    __tablename__ = "patient_conditions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    condition_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    icd10_code: Mapped[str | None] = mapped_column(String(10), index=True)
    severity: Mapped[str] = mapped_column(String(30), nullable=False, default="moderate")
    diagnosis_date: Mapped[datetime | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    treatment_notes: Mapped[str | None] = mapped_column(Text)
    current_medications: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    is_chronic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    patient: Mapped["Patient"] = relationship("Patient", back_populates="conditions")
