"""
MCP Tools — Clinical, Administrative, and Regulatory tools.

Available tools:
- check_drug_interactions: Drug-drug interaction checker
- get_patient_history: Patient medical history retrieval
- check_halal_compliance: Halal certification checker (SEA-specific)
- verify_prescription: Prescription verification (SEA regulations)
"""

from .drug_interactions import check_drug_interactions
from .halal_compliance import check_halal_compliance
from .patient_history import get_patient_history
from .prescription_verification import verify_prescription
from .pharmacy_operations import (
    get_expiring_inventory,
    get_inventory_overview,
    get_pharmacy_workflow_guide,
    get_sales_summary,
    search_pharmacy_products,
)

__all__ = [
    "check_drug_interactions",
    "get_patient_history",
    "check_halal_compliance",
    "verify_prescription",
    "search_pharmacy_products",
    "get_inventory_overview",
    "get_pharmacy_workflow_guide",
    "get_expiring_inventory",
    "get_sales_summary",
]
