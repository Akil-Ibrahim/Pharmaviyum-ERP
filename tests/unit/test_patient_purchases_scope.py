"""Tenant-scope regression tests for patient purchase read API."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.dialects import postgresql

from src.pharmaviyum.api.v1.patient_purchases import list_patient_purchases

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_patient_purchase_read_requires_and_applies_pharmacy_scope():
    session = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    session.execute.return_value = result

    purchases = await list_patient_purchases(
        _=object(),
        db=session,
        skip=0,
        limit=50,
        pharmacy_id=731,
    )

    statement = session.execute.await_args.args[0]
    sql = str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )

    assert "JOIN patients" in sql
    assert "patients.pharmacy_id = 731" in sql
    assert purchases == []


@pytest.mark.asyncio
async def test_patient_purchase_read_does_not_return_unscoped_rows():
    session = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    session.execute.return_value = result

    await list_patient_purchases(
        _=object(),
        db=session,
        skip=0,
        limit=50,
        pharmacy_id=731,
    )

    statement = session.execute.await_args.args[0]
    where_clause = str(
        statement.whereclause.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )
    assert "patients.pharmacy_id = 731" in where_clause
