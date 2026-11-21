"""Schema allowlist tests for patient-facing response contracts."""

import pytest

from src.pharmaviyum.schemas.patient import (
    PatientAIProfile,
    PatientSummaryResponse,
)

pytestmark = pytest.mark.unit


def test_patient_summary_has_an_explicit_nonclinical_field_allowlist():
    assert set(PatientSummaryResponse.model_fields) == {
        "id",
        "first_name",
        "last_name",
        "full_name",
        "phone",
        "email",
        "city",
        "country",
        "customer_category",
        "loyalty_tier",
        "loyalty_points",
        "visit_count",
        "is_active",
        "created_at",
        "updated_at",
    }


def test_patient_ai_profile_has_only_clinical_safety_context_fields():
    assert set(PatientAIProfile.model_fields) == {
        "patient_id",
        "allergies",
        "conditions",
    }
