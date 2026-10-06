"""Regression tests for Dashboard tenant query scoping."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.dialects import postgresql

from src.pharmaviyum.api.v1 import dashboard


class _Result:
    def __init__(self, rows=None):
        self._rows = rows or []

    def all(self):
        return self._rows

    def one(self):
        return SimpleNamespace(
            tracked=0,
            expired=0,
            critical=0,
            warning=0,
            extended_warning=0,
        )


class _Session:
    def __init__(self):
        self.scalar = AsyncMock(return_value=0)
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        return _Result()


@pytest.mark.asyncio
async def test_dashboard_summary_applies_one_pharmacy_scope_to_all_aggregates():
    """Every Dashboard aggregate must be constrained to the resolved pharmacy."""
    session = _Session()
    user = SimpleNamespace(id=100, is_active=True, is_superuser=False)

    with patch.object(
        dashboard,
        "resolve_pharmacy_scope",
        new=AsyncMock(return_value=42),
    ):
        result = await dashboard.get_dashboard_summary(
            current_user=user,
            session=session,
            pharmacy_id=42,
        )

    assert result["patients"]["active"] == 0
    assert result["sales"]["today"] == 0
    assert result["inventory"]["items"] == 0

    sql_statements = [
        str(statement.compile(dialect=postgresql.dialect()))
        for statement in session.statements
    ]

    # The five execute-based Dashboard aggregates must all carry the
    # patient/pharmacy boundary or direct inventory pharmacy boundary.
    patient_queries = [
        sql
        for sql in sql_statements
        if "patient_purchases" in sql
    ]
    assert len(patient_queries) >= 4
    assert all("patients.pharmacy_id" in sql for sql in patient_queries)

    inventory_queries = [
        sql
        for sql in sql_statements
        if "inventory" in sql
    ]
    assert inventory_queries
    assert all("inventory.pharmacy_id" in sql for sql in inventory_queries)

    # Scalar queries are also part of the captured session contract.
    scalar_sql = [
        str(statement.compile(dialect=postgresql.dialect()))
        for statement in session.scalar.await_args_list
    ]
    assert any("patients.pharmacy_id" in sql for sql in scalar_sql)
    assert any("inventory.pharmacy_id" in sql for sql in scalar_sql)
