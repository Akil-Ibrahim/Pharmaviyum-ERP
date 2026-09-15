"""
MCP Tool Schemas — structured inputs/outputs for all tools.

Best practice 2026:
- Pydantic v2 with strict validation
- Discriminated unions for polymorphic responses
- Frozen models for immutability across tool boundaries
- Medical-specific types (drug names, dosages, interactions)
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# DRUG INTERACTION TOOL
# ============================================================================


class DrugInteractionCheck(BaseModel):
    """Input for drug interaction checker."""

    model_config = ConfigDict(frozen=True)

    drug_names: list[str] = Field(..., min_length=2, max_length=20)
    country: str = Field(default="VN", description="ISO country code")
    patient_id: int | None = None
    include_severity: bool = True
    include_alternatives: bool = True


class DrugInteraction(BaseModel):
    """Single drug-drug interaction."""

    model_config = ConfigDict(frozen=True)

    drug_a: str
    drug_b: str
    severity: Literal["low", "moderate", "high", "critical"]
    mechanism: str | None = None
    clinical_effect: str
    management: str
    source: str
    evidence_level: Literal["A", "B", "C", "D"] = "C"


class InteractionCheckResult(BaseModel):
    """Result of drug interaction check."""

    model_config = ConfigDict(frozen=True)

    drugs_checked: list[str]
    interactions: list[DrugInteraction] = Field(default_factory=list)
    overall_severity: Literal["none", "low", "moderate", "high", "critical"]
    recommendations: list[str] = Field(default_factory=list)
    alternatives: dict[str, list[str]] = Field(default_factory=dict)
    sources: list[str] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# PATIENT HISTORY TOOL
# ============================================================================


class PatientHistoryRequest(BaseModel):
    """Input for patient history retrieval."""

    model_config = ConfigDict(frozen=True)

    patient_id: int
    include_allergies: bool = True
    include_conditions: bool = True
    include_prescriptions: bool = True
    include_orders: bool = False
    months_back: int = Field(default=12, ge=1, le=120)


class AllergyInfo(BaseModel):
    model_config = ConfigDict(frozen=True)
    allergen: str
    type: Literal["drug", "food", "environmental"]
    severity: Literal["mild", "moderate", "severe"]
    verified: bool = False


class ConditionInfo(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    icd10_code: str | None = None
    is_chronic: bool = False
    status: Literal["active", "resolved", "managed"] = "active"


class PatientHistory(BaseModel):
    """Patient medical history summary."""

    model_config = ConfigDict(frozen=True)

    patient_id: int
    full_name: str
    age: int | None = None
    gender: str | None = None
    blood_type: str | None = None
    allergies: list[AllergyInfo] = Field(default_factory=list)
    conditions: list[ConditionInfo] = Field(default_factory=list)
    active_prescriptions: int = 0
    recent_orders: int = 0
    loyalty_tier: str | None = None
    preferred_language: str = "vi"


# ============================================================================
# HALAL COMPLIANCE TOOL
# ============================================================================


class HalalCheckRequest(BaseModel):
    """Input for halal compliance check."""

    model_config = ConfigDict(frozen=True)

    drug_name: str
    country: str = Field(default="VN")
    include_alternatives: bool = True


class HalalCertification(BaseModel):
    """Halal certification details."""

    model_config = ConfigDict(frozen=True)

    drug_name: str
    is_halal: bool
    certification_body: str | None = None
    certificate_number: str | None = None
    valid_until: date | None = None
    ingredients_concern: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    notes: str | None = None


# ============================================================================
# PRESCRIPTION VERIFICATION TOOL
# ============================================================================


class PrescriptionVerifyRequest(BaseModel):
    """Input for prescription verification."""

    model_config = ConfigDict(frozen=True)

    prescription_number: str
    pharmacist_id: int
    checks: list[
        Literal[
            "expiry",
            "prescriber_license",
            "quantity_limits",
            "duplicate_dispensing",
            "drug_availability",
            "interactions",
        ]
    ] = Field(
        default_factory=lambda: [
            "expiry",
            "prescriber_license",
            "quantity_limits",
            "duplicate_dispensing",
        ]
    )


class PrescriptionCheck(BaseModel):
    """Single prescription check result."""

    model_config = ConfigDict(frozen=True)

    check_type: str
    passed: bool
    details: str | None = None
    warnings: list[str] = Field(default_factory=list)


class PrescriptionVerification(BaseModel):
    """Full prescription verification result."""

    model_config = ConfigDict(frozen=True)

    prescription_number: str
    is_valid: bool
    checks: list[PrescriptionCheck] = Field(default_factory=list)
    patient_name: str | None = None
    prescriber_name: str | None = None
    drugs: list[str] = Field(default_factory=list)
    overall_warnings: list[str] = Field(default_factory=list)
    verified_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# GENERIC MCP RESPONSE
# ============================================================================


class MCPToolResponse(BaseModel):
    """Standardized MCP tool response wrapper."""

    model_config = ConfigDict(frozen=True)

    tool_name: str
    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    latency_ms: float = 0.0
