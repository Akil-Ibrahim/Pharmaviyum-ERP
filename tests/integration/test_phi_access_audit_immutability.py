"""PostgreSQL enforcement tests for immutable PHI access audit records."""

import pytest
from sqlalchemy import delete, select, text, update
from sqlalchemy.exc import DBAPIError

from src.pharmaviyum.models.phi_access_audit import PHIAccessAudit


@pytest.mark.integration
@pytest.mark.parametrize("mutation", ["update", "delete"])
async def test_phi_access_audit_records_are_append_only(test_db, mutation):
    # The shared integration fixture uses Base.metadata.create_all(), which does
    # not execute Alembic migrations. Install the same trigger defined by
    # 2026_11_21_000001_phi_access_audit.py in this isolated test database.
    await test_db.execute(
        text(
            """
            CREATE FUNCTION reject_phi_access_audit_mutation() RETURNS trigger
            LANGUAGE plpgsql AS $$
            BEGIN
                RAISE EXCEPTION 'phi_access_audits is append-only';
            END;
            $$
            """
        )
    )
    await test_db.execute(
        text(
            """
            CREATE TRIGGER trg_phi_access_audits_append_only
            BEFORE UPDATE OR DELETE ON phi_access_audits
            FOR EACH ROW EXECUTE FUNCTION reject_phi_access_audit_mutation()
            """
        )
    )

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
