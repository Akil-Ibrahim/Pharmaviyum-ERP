"""PostgreSQL enforcement tests for immutable PHI access audit records."""

import pytest
from sqlalchemy import delete, select, update
from sqlalchemy.exc import DBAPIError

from src.pharmaviyum.models.phi_access_audit import PHIAccessAudit


@pytest.mark.integration
@pytest.mark.parametrize("mutation", ["update", "delete"])
async def test_phi_access_audit_records_are_append_only(test_db, mutation):
    audit = PHIAccessAudit(
        actor_id=9001,
        pharmacy_id=9002,
        patient_id=9003,
        action="read_ai_patient_profile",
        decision="allowed",
        purpose="dispensing_review",
        request_id=f"immutability-{mutation}",
    )
    test_db.add(audit)
    await test_db.flush()
    audit_id = audit.id
    await test_db.commit()

    statement = (
        update(PHIAccessAudit)
        .where(PHIAccessAudit.id == audit_id)
        .values(purpose="tampered")
        if mutation == "update"
        else delete(PHIAccessAudit).where(PHIAccessAudit.id == audit_id)
    )

    with pytest.raises(DBAPIError) as exc_info:
        await test_db.execute(statement)

    assert "phi_access_audits is append-only" in str(exc_info.value.orig)
    await test_db.rollback()

    persisted = await test_db.scalar(
        select(PHIAccessAudit).where(PHIAccessAudit.id == audit_id)
    )
    assert persisted is not None
    assert persisted.purpose == "dispensing_review"
    assert persisted.request_id == f"immutability-{mutation}"
