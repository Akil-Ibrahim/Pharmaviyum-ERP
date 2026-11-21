"""Tenant-scope regression tests for patient repository query builders."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.dialects import postgresql

from src.pharmaviyum.repositories.patient import PatientRepository

pytestmark = pytest.mark.unit

PHARMACY_ID = 731


def _sql(statement) -> str:
    return str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


@pytest.mark.asyncio
async def test_recent_patients_query_is_scoped_to_pharmacy():
    session = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    session.execute.return_value = result

    repository = PatientRepository(session)
    await repository.get_recent_patients(pharmacy_id=PHARMACY_ID)

    statement = session.execute.await_args.args[0]
    assert f"patients.pharmacy_id = {PHARMACY_ID}" in _sql(statement)


@pytest.mark.asyncio
async def test_top_customers_query_is_scoped_to_pharmacy():
    session = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    session.execute.return_value = result

    repository = PatientRepository(session)
    await repository.get_top_customers(pharmacy_id=PHARMACY_ID)

    statement = session.execute.await_args.args[0]
    assert f"patients.pharmacy_id = {PHARMACY_ID}" in _sql(statement)


@pytest.mark.asyncio
async def test_soft_delete_uses_scoped_lookup_instead_of_unscoped_get_by_id():
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute.return_value = result

    repository = PatientRepository(session)
    deleted = await repository.soft_delete(42, pharmacy_id=PHARMACY_ID)

    statement = session.execute.await_args.args[0]
    assert f"patients.pharmacy_id = {PHARMACY_ID}" in _sql(statement)
    assert deleted is False
    session.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_record_visit_uses_scoped_lookup_instead_of_unscoped_get_by_id():
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute.return_value = result

    repository = PatientRepository(session)
    patient = await repository.record_visit(42, pharmacy_id=PHARMACY_ID)

    statement = session.execute.await_args.args[0]
    assert f"patients.pharmacy_id = {PHARMACY_ID}" in _sql(statement)
    assert patient is None
    session.flush.assert_not_awaited()
