"""Pharmaviyum CRM database models."""

from src.pharmaviyum.models.drug_catalog import (
    DrugCatalogSourceRecord,
    DrugReference,
    DrugReferenceIngredient,
    MedicinalProduct,
)

# Import POS entities so Alembic registers their tables in Base.metadata.
from src.pharmaviyum.models.pos import Payment, Sale, SaleItem, SaleItemAllocation
from src.pharmaviyum.models.user import User
from src.pharmaviyum.models.user_avatar import UserAvatar
