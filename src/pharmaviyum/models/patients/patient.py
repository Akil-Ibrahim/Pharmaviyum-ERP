"""Patient domain entity."""

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.pharmaviyum.db.base import Base
from src.pharmaviyum.models.patients.consultation import Consultation
from src.pharmaviyum.models.patients.patient_allergy import PatientAllergy
from src.pharmaviyum.models.patients.patient_condition import PatientCondition
from src.pharmaviyum.models.patients.patient_insurance import PatientInsurance
from src.pharmaviyum.models.patients.patient_purchase import PatientPurchase


class Patient(Base):
    """Canonical person/patient record used by pharmacy workflows."""

    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pharmacy_id: Mapped[int | None] = mapped_column(Integer, index=True)
    external_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, index=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(String(20))
    phone: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True, index=True
    )
    email: Mapped[str | None] = mapped_column(String(200), index=True)
    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(100), index=True)
    country: Mapped[str] = mapped_column(
        String(2), nullable=False, default="US", index=True
    )
    postal_code: Mapped[str | None] = mapped_column(String(20))
    national_id: Mapped[str | None] = mapped_column(String(50))
    insurance_number: Mapped[str | None] = mapped_column(String(50))
    allergies_notes: Mapped[str | None] = mapped_column(Text)
    chronic_conditions: Mapped[str | None] = mapped_column(Text)
    blood_type: Mapped[str | None] = mapped_column(String(5))
    preferred_language: Mapped[str] = mapped_column(
        String(5), nullable=False, default="en"
    )
    preferred_notification_channel: Mapped[str] = mapped_column(
        String(20), nullable=False, default="email"
    )
    customer_category: Mapped[str] = mapped_column(
        String(50), nullable=False, default="General", index=True
    )
    loyalty_tier: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Bronze"
    )
    loyalty_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    visit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_visit_date: Mapped[datetime | None] = mapped_column(DateTime)
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )
    pos_system: Mapped[str | None] = mapped_column(String(50))
    synced_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    allergies: Mapped[list["PatientAllergy"]] = relationship(
        "PatientAllergy", back_populates="patient", cascade="all, delete-orphan"
    )
    conditions: Mapped[list["PatientCondition"]] = relationship(
        "PatientCondition", back_populates="patient", cascade="all, delete-orphan"
    )
    insurances: Mapped[list["PatientInsurance"]] = relationship(
        "PatientInsurance", back_populates="patient", cascade="all, delete-orphan"
    )
    consultations: Mapped[list["Consultation"]] = relationship(
        "Consultation", back_populates="patient", cascade="all, delete-orphan"
    )
    purchases: Mapped[list["PatientPurchase"]] = relationship(
        "PatientPurchase", back_populates="patient", cascade="all, delete-orphan"
    )
