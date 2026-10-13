from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
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
