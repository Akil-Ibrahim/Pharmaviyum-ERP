"""PostgreSQL migration tests for immutable PHI access audit records."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.pharmaviyum.models.phi_access_audit import PHIAccessAudit


@pytest.fixture
async def migrated_phi_audit_db():
    """Use the separate PostgreSQL database upgraded by the CI Alembic step."""
    database_url = os.getenv("MIGRATION_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("MIGRATION_TEST_DATABASE_URL is required for migration tests")

    engine = create_async_engine(database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    try:
        async with session_factory() as session:
            yield session
    finally:
        await engine.dispose()


@pytest.mark.integration
@pytest.mark.parametrize("mutation", ["update", "delete", "truncate"])
async def test_phi_access_audit_migration_enforces_append_only(
    migrated_phi_audit_db, mutation
):
    """The actual Alembic migration must reject row and table mutations."""
    db = migrated_phi_audit_db
    audit = PHIAccessAudit(
        actor_id=9901,
        pharmacy_id=9902,
        patient_id=9903,
        action="read_ai_patient_profile",
        decision="allowed",
        purpose="dispensing_review",
        request_id=f"phi-audit-immutability-{mutation}",
    )
    db.add(audit)
    await db.commit()
    audit_id = audit.id

    statements = {
        "update": (
            "UPDATE phi_access_audits SET purpose = 'tampered' WHERE id = :id",
            {"id": audit_id},
        ),
        "delete": (
            "DELETE FROM phi_access_audits WHERE id = :id",
            {"id": audit_id},
        ),
        "truncate": ("TRUNCATE TABLE phi_access_audits", {}),
    }
    statement, parameters = statements[mutation]
    with pytest.raises(DBAPIError) as exc_info:
        await db.execute(text(statement), parameters)

    assert "phi_access_audits is append-only" in str(exc_info.value.orig)
    await db.rollback()

    persisted = await db.scalar(
        select(PHIAccessAudit).where(PHIAccessAudit.id == audit_id)
    )
    assert persisted is not None
    assert persisted.purpose == "dispensing_review"
    assert persisted.request_id == f"phi-audit-immutability-{mutation}"
