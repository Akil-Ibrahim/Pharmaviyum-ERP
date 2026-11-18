"""Regulatory reference models for medical devices."""

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.pharmaviyum.db.base import Base


class MedicalDevice(Base):
    """A source-specific medical-device reference record."""

    __tablename__ = "medical_devices"
    __table_args__ = (
        UniqueConstraint(
            "source_name",
            "source_record_id",
            name="uq_medical_device_source_record",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_record_id: Mapped[str] = mapped_column(String(160), nullable=False)
    source_version: Mapped[str | None] = mapped_column(String(160), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    license_terms: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    country: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    brand_name: Mapped[str | None] = mapped_column(
        String(200), nullable=True, index=True
    )
    model: Mapped[str | None] = mapped_column(String(200), nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(
        String(250), nullable=True, index=True
    )
    manufacturer_country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    device_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    risk_class: Mapped[str | None] = mapped_column(
        String(40), nullable=True, index=True
    )
    intended_purpose: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    regulatory_status: Mapped[str | None] = mapped_column(String(80), nullable=True)
    source_updated_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    identifiers: Mapped[list["MedicalDeviceIdentifier"]] = relationship(
        back_populates="medical_device",
        cascade="all, delete-orphan",
        order_by="MedicalDeviceIdentifier.id",
    )
    authorizations: Mapped[list["MedicalDeviceAuthorization"]] = relationship(
        back_populates="medical_device",
        cascade="all, delete-orphan",
        order_by="MedicalDeviceAuthorization.id",
    )


class MedicalDeviceIdentifier(Base):
    """UDI-DI and other regulatory identifiers for a device record."""

    __tablename__ = "medical_device_identifiers"
    __table_args__ = (
        UniqueConstraint(
            "medical_device_id",
            "identifier_type",
            "identifier_value",
            name="uq_medical_device_identifier",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    medical_device_id: Mapped[int] = mapped_column(
        ForeignKey("medical_devices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    identifier_type: Mapped[str] = mapped_column(String(60), nullable=False)
    identifier_value: Mapped[str] = mapped_column(
        String(160), nullable=False, index=True
    )
    issuing_agency: Mapped[str | None] = mapped_column(String(40), nullable=True)
    is_primary: Mapped[bool] = mapped_column(default=False, nullable=False)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )

    medical_device: Mapped["MedicalDevice"] = relationship(back_populates="identifiers")


class MedicalDeviceAuthorization(Base):
    """A country-specific licence or authorization for a device record."""

    __tablename__ = "medical_device_authorizations"
    __table_args__ = (
        UniqueConstraint(
            "medical_device_id",
            "country",
            "authorization_id",
            name="uq_medical_device_authorization",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    medical_device_id: Mapped[int] = mapped_column(
        ForeignKey("medical_devices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    country: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    authorization_id: Mapped[str] = mapped_column(String(120), nullable=False)
    authorization_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str | None] = mapped_column(String(80), nullable=True)
    risk_class: Mapped[str | None] = mapped_column(String(40), nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_updated_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )

    medical_device: Mapped["MedicalDevice"] = relationship(
        back_populates="authorizations"
    )
