"""Tenant authorization and PHI audit tests for AI patient profile reads."""

import pytest
from sqlalchemy import select

from src.pharmaviyum.core.oauth2 import create_access_token
from src.pharmaviyum.models.pharmacy import Pharmacy
from src.pharmaviyum.models.pharmacy_membership import PharmacyMembership
from src.pharmaviyum.models.phi_access_audit import PHIAccessAudit
from src.pharmaviyum.models.user import User


async def _authenticate_as_pharmacist(client, test_db):
    user = User(
        id=2,
        email="ai-profile-pharmacist@example.com",
        username="ai-profile-pharmacist",
        hashed_password="not-used-in-tests",
        is_active=True,
        is_superuser=False,
    )
    test_db.add(user)
    await test_db.flush()
    client.headers["Authorization"] = f"Bearer {create_access_token(str(user.id))}"
    return client


@pytest.mark.integration
async def test_ai_patient_profile_requires_membership_and_audits_allowed_read(
    authenticated_client, test_db, patient_factory
):
    client = await _authenticate_as_pharmacist(authenticated_client, test_db)
    pharmacy = Pharmacy(name="AI Profile Pharmacy A", code="AI-PROFILE-A")
    test_db.add(pharmacy)
    await test_db.flush()
    patient = await patient_factory.create(pharmacy_id=pharmacy.id)
    test_db.add(
        PharmacyMembership(user_id=2, pharmacy_id=pharmacy.id, is_active=True)
    )
    await test_db.flush()

    response = await client.get(
        f"/api/v1/patients/{patient.id}/ai-profile",
        params={
            "pharmacy_id": pharmacy.id,
            "purpose": "dispensing_review",
        },
        headers={"x-request-id": "ai-profile-test-request"},
    )

    assert response.status_code == 200, response.text
    assert set(response.json()) == {"patient_id", "allergies", "conditions"}
    audit = await test_db.scalar(
        select(PHIAccessAudit).where(
            PHIAccessAudit.patient_id == patient.id,
            PHIAccessAudit.action == "read_ai_patient_profile",
            PHIAccessAudit.decision == "allowed",
        )
    )
    assert audit is not None
    assert (
        audit.actor_id,
        audit.pharmacy_id,
        audit.purpose,
        audit.request_id,
    ) == (2, pharmacy.id, "dispensing_review", "ai-profile-test-request")


@pytest.mark.integration
async def test_ai_patient_profile_denies_missing_membership_and_audits_denial(
    authenticated_client, test_db, patient_factory
):
    client = await _authenticate_as_pharmacist(authenticated_client, test_db)
    pharmacy = Pharmacy(name="AI Profile Pharmacy B", code="AI-PROFILE-B")
    test_db.add(pharmacy)
    await test_db.flush()
    patient = await patient_factory.create(pharmacy_id=pharmacy.id)

    response = await client.get(
        f"/api/v1/patients/{patient.id}/ai-profile",
        params={"pharmacy_id": pharmacy.id, "purpose": "patient_request"},
    )

    assert response.status_code == 403
    audit = await test_db.scalar(
        select(PHIAccessAudit).where(
            PHIAccessAudit.patient_id == patient.id,
            PHIAccessAudit.action == "read_ai_patient_profile",
            PHIAccessAudit.decision == "denied",
        )
    )
    assert audit is not None
    assert audit.actor_id == 2


@pytest.mark.integration
async def test_ai_patient_profile_rejects_cross_pharmacy_patient_and_audits_denial(
    authenticated_client, test_db, patient_factory
):
    client = await _authenticate_as_pharmacist(authenticated_client, test_db)
    pharmacy_a = Pharmacy(name="AI Profile Pharmacy C", code="AI-PROFILE-C")
    pharmacy_b = Pharmacy(name="AI Profile Pharmacy D", code="AI-PROFILE-D")
    test_db.add_all([pharmacy_a, pharmacy_b])
    await test_db.flush()
    patient = await patient_factory.create(pharmacy_id=pharmacy_b.id)
    test_db.add(
        PharmacyMembership(user_id=2, pharmacy_id=pharmacy_a.id, is_active=True)
    )
    await test_db.flush()

    response = await client.get(
        f"/api/v1/patients/{patient.id}/ai-profile",
        params={"pharmacy_id": pharmacy_a.id, "purpose": "medication_reconciliation"},
    )

    assert response.status_code == 404
    audit = await test_db.scalar(
        select(PHIAccessAudit).where(
            PHIAccessAudit.patient_id == patient.id,
            PHIAccessAudit.action == "read_ai_patient_profile",
            PHIAccessAudit.decision == "denied",
        )
    )
    assert audit is not None
    assert audit.pharmacy_id == pharmacy_a.id


@pytest.mark.integration
async def test_ai_patient_profile_denies_platform_superuser_and_audits_denial(
    authenticated_client, test_db, patient_factory
):
    pharmacy = Pharmacy(name="AI Profile Pharmacy E", code="AI-PROFILE-E")
    test_db.add(pharmacy)
    await test_db.flush()
    patient = await patient_factory.create(pharmacy_id=pharmacy.id)

    response = await authenticated_client.get(
        f"/api/v1/patients/{patient.id}/ai-profile",
        params={"pharmacy_id": pharmacy.id, "purpose": "patient_request"},
    )

    assert response.status_code == 403
    audit = await test_db.scalar(
        select(PHIAccessAudit).where(
            PHIAccessAudit.patient_id == patient.id,
            PHIAccessAudit.action == "read_ai_patient_profile",
            PHIAccessAudit.decision == "denied",
        )
    )
    assert audit is not None
    assert audit.actor_id == 1
