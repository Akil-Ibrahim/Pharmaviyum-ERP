"""PostgreSQL integration tests for pharmacist patient-history isolation."""

from datetime import datetime

import pytest
from sqlalchemy import select

from src.pharmaviyum.models.pharmacy import Pharmacy
from src.pharmaviyum.models.pharmacy_membership import PharmacyMembership
from src.pharmaviyum.models.patients import PatientPurchase
from src.pharmaviyum.models.phi_access_audit import PHIAccessAudit


@pytest.mark.integration
async def test_patient_history_returns_minimal_fields_and_audits_allowed_read(
    authenticated_client, test_db, patient_factory
):
    pharmacy = Pharmacy(name="History Pharmacy A", code="HISTORY-A")
    test_db.add(pharmacy)
    await test_db.flush()
    patient = await patient_factory.create(pharmacy_id=pharmacy.id)
    test_db.add(
        PharmacyMembership(
            user_id=1, pharmacy_id=pharmacy.id, is_active=True
        )
    )
    test_db.add(
        PatientPurchase(
            patient_id=patient.id,
            receipt_number="HISTORY-RECEIPT-1",
            category="medicine",
            quantity=2,
            dispensed_packs=2,
            dispensed_blisters=0,
            dispensed_units=0,
            unit_price=10.0,
            prescription_required=False,
            purchased_at=datetime.utcnow(),
        )
    )
    await test_db.flush()

    response = await authenticated_client.get(
        f"/api/v1/patient-purchases/{patient.id}/history",
        params={
            "pharmacy_id": pharmacy.id,
            "purpose": "medication_reconciliation",
        },
    )

    assert response.status_code == 200, response.text
    rows = response.json()
    assert len(rows) == 1
    assert set(rows[0]) == {"id", "product_name", "category", "quantity", "purchased_at"}
    audit = await test_db.scalar(
        select(PHIAccessAudit).where(
            PHIAccessAudit.patient_id == patient.id,
            PHIAccessAudit.decision == "allowed",
        )
    )
    assert audit is not None
    assert audit.actor_id == 1
    assert audit.pharmacy_id == pharmacy.id
    assert audit.purpose == "medication_reconciliation"


@pytest.mark.integration
async def test_patient_history_rejects_cross_pharmacy_patient_and_audits_denial(
    authenticated_client, test_db, patient_factory
):
    pharmacy_a = Pharmacy(name="History Pharmacy B", code="HISTORY-B")
    pharmacy_b = Pharmacy(name="History Pharmacy C", code="HISTORY-C")
    test_db.add_all([pharmacy_a, pharmacy_b])
    await test_db.flush()
    patient_b = await patient_factory.create(pharmacy_id=pharmacy_b.id)
    test_db.add(
        PharmacyMembership(
            user_id=1, pharmacy_id=pharmacy_a.id, is_active=True
        )
    )
    await test_db.flush()

    response = await authenticated_client.get(
        f"/api/v1/patient-purchases/{patient_b.id}/history",
        params={
            "pharmacy_id": pharmacy_a.id,
            "purpose": "dispensing_review",
        },
    )

    assert response.status_code == 404
    audit = await test_db.scalar(
        select(PHIAccessAudit).where(
            PHIAccessAudit.patient_id == patient_b.id,
            PHIAccessAudit.decision == "denied",
        )
    )
    assert audit is not None
    assert audit.pharmacy_id == pharmacy_a.id
    assert audit.purpose == "dispensing_review"


@pytest.mark.integration
async def test_patient_history_rejects_missing_pharmacy_membership(
    authenticated_client, test_db, patient_factory
):
    pharmacy = Pharmacy(name="History Pharmacy D", code="HISTORY-D")
    test_db.add(pharmacy)
    await test_db.flush()
    patient = await patient_factory.create(pharmacy_id=pharmacy.id)

    response = await authenticated_client.get(
        f"/api/v1/patient-purchases/{patient.id}/history",
        params={
            "pharmacy_id": pharmacy.id,
            "purpose": "patient_request",
        },
    )

    assert response.status_code == 403
    audit = await test_db.scalar(
        select(PHIAccessAudit).where(
            PHIAccessAudit.patient_id == patient.id,
            PHIAccessAudit.decision == "denied",
        )
    )
    assert audit is not None
    assert audit.actor_id == 1
