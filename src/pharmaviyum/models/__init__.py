"""Pharmaviyum CRM database models."""

from src.pharmaviyum.models.drug_catalog import (
    DrugCatalogSourceRecord,
    DrugReference,
    DrugReferenceIngredient,
    MedicinalProduct,
)
from src.pharmaviyum.models.outbox import OutboxEvent

# Import POS entities so Alembic registers their tables in Base.metadata.
from src.pharmaviyum.models.pos import Payment, Sale, SaleItem, SaleItemAllocation
from src.pharmaviyum.models.sync import CentralInboxEvent, PharmacyEdgeNode
from src.pharmaviyum.models.user import User
from src.pharmaviyum.models.user_avatar import UserAvatar

# Explicit exports keep these model imports available for Alembic metadata discovery.
__all__ = [
    "CentralInboxEvent",
    "DrugCatalogSourceRecord",
    "DrugReference",
    "DrugReferenceIngredient",
    "MedicinalProduct",
    "OutboxEvent",
    "Payment",
    "PharmacyEdgeNode",
    "Sale",
    "SaleItem",
    "SaleItemAllocation",
    "User",
    "UserAvatar",
]
