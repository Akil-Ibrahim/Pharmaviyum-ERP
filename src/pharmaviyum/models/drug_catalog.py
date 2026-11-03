from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.pharmaviyum.db.base import Base


class DrugReference(Base):
    __tablename__ = "drug_references"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    inn_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    atc_code: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    ingredients: Mapped[list["DrugReferenceIngredient"]] = relationship(
        back_populates="drug_reference", cascade="all, delete-orphan"
    )
    medicinal_products: Mapped[list["MedicinalProduct"]] = relationship(
        back_populates="drug_reference", cascade="all, delete-orphan"
    )


class DrugReferenceIngredient(Base):
    __tablename__ = "drug_reference_ingredients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    drug_reference_id: Mapped[int] = mapped_column(
        ForeignKey("drug_references.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ingredient_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)

    drug_reference: Mapped["DrugReference"] = relationship(back_populates="ingredients")


class MedicinalProduct(Base):
    __tablename__ = "medicinal_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    drug_reference_id: Mapped[int] = mapped_column(
        ForeignKey("drug_references.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    brand_name: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    product_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="generic"
    )
    manufacturer: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    strength: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dosage_form: Mapped[str | None] = mapped_column(String(100), nullable=True)
    route: Mapped[str | None] = mapped_column(String(100), nullable=True)
    package_description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    gtin: Mapped[str | None] = mapped_column(String(14), nullable=True, index=True)
    regulatory_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    authorization_country: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    drug_reference: Mapped["DrugReference"] = relationship(
        back_populates="medicinal_products"
    )


class DrugCatalogSourceRecord(Base):
    """A provenance-preserving external record awaiting catalog review."""

    __tablename__ = "drug_catalog_source_records"
    __table_args__ = (
        UniqueConstraint(
            "source_name",
            "source_record_id",
            "source_version",
            name="uq_drug_catalog_source_identity",
        ),
        CheckConstraint(
            "review_status IN ('pending_review', 'approved', 'rejected', 'duplicate')",
            name="ck_drug_catalog_source_review_status",
        ),
        CheckConstraint(
            "match_confidence IS NULL OR "
            "(match_confidence >= 0 AND match_confidence <= 1)",
            name="ck_drug_catalog_source_match_confidence",
        ),
        CheckConstraint(
            "matched_drug_reference_id IS NULL OR "
            "matched_medicinal_product_id IS NULL",
            name="ck_drug_catalog_source_single_match_target",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_record_id: Mapped[str] = mapped_column(String(150), nullable=False)
    source_version: Mapped[str] = mapped_column(String(100), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    license_terms: Mapped[str | None] = mapped_column(String(500), nullable=True)
    extracted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    normalized_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    review_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending_review", index=True
    )
    match_confidence: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    matched_drug_reference_id: Mapped[int | None] = mapped_column(
        ForeignKey("drug_references.id", ondelete="SET NULL"), nullable=True, index=True
    )
    matched_medicinal_product_id: Mapped[int | None] = mapped_column(
        ForeignKey("medicinal_products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reviewed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    review_notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    matched_drug_reference: Mapped["DrugReference | None"] = relationship()
    matched_medicinal_product: Mapped["MedicinalProduct | None"] = relationship()
    reviewed_by: Mapped["User | None"] = relationship()
