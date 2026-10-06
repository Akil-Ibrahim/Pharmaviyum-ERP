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

    # Patient-backed aggregates must constrain the joined Patient table.
    patient_queries = [sql for sql in sql_statements if "patient_purchases" in sql]
    assert len(patient_queries) >= 4
    assert all("patients.pharmacy_id = " in sql for sql in patient_queries)

    # Inventory aggregates must constrain Inventory directly. The top-products
    # stock scalar subquery is also checked through this contract.
    inventory_queries = [sql for sql in sql_statements if "inventory" in sql]
    assert inventory_queries
    assert all("pharmacy_id = " in sql for sql in inventory_queries)

    # The resolved tenant value must be bound to the same SQL predicate rather
    # than merely mentioning a pharmacy column.
    patient_params = [
        statement.compile(dialect=postgresql.dialect()).params
        for statement in session.statements
        if "patient_purchases" in str(
            statement.compile(dialect=postgresql.dialect())
        )
    ]
    assert all(42 in params.values() for params in patient_params)

    inventory_params = [
        statement.compile(dialect=postgresql.dialect()).params
        for statement in session.statements
        if "inventory" in str(statement.compile(dialect=postgresql.dialect()))
    ]
    assert all(42 in params.values() for params in inventory_params)

    # Scalar queries are also part of the captured session contract.
    scalar_sql = [
        str(call.args[0].compile(dialect=postgresql.dialect()))
        for call in session.scalar.await_args_list
    ]
    assert any("patients.pharmacy_id" in sql for sql in scalar_sql)
    assert any("inventory.pharmacy_id" in sql for sql in scalar_sql)


@pytest.mark.asyncio
async def test_dashboard_summary_keeps_superuser_global_scope_unfiltered():
    """A superuser global scope must not add a pharmacy filter."""
    session = _Session()
    user = SimpleNamespace(id=1, is_active=True, is_superuser=True)

    with patch.object(
        dashboard,
        "resolve_pharmacy_scope",
        new=AsyncMock(return_value=None),
    ):
        await dashboard.get_dashboard_summary(
            current_user=user,
            session=session,
            pharmacy_id=None,
        )

    sql_statements = [
        str(statement.compile(dialect=postgresql.dialect()))
        for statement in session.statements
    ]
    scalar_sql = [
        str(call.args[0].compile(dialect=postgresql.dialect()))
        for call in session.scalar.await_args_list
    ]
    all_sql = sql_statements + scalar_sql
    assert all("pharmacy_id" not in sql for sql in all_sql)


@pytest.mark.asyncio
async def test_dashboard_patient_condition_prefers_active_status():
    """Dashboard must prefer an active condition over a stale inactive one."""
    session = _Session()
    user = SimpleNamespace(id=100, is_active=True, is_superuser=False)

    with patch.object(
        dashboard,
        "resolve_pharmacy_scope",
        new=AsyncMock(return_value=42),
    ):
        await dashboard.get_dashboard_summary(
            current_user=user,
            session=session,
            pharmacy_id=42,
        )

    medication_sql = next(
        sql
        for sql in (
            str(statement.compile(dialect=postgresql.dialect()))
            for statement in session.statements
        )
        if "patient_conditions" in sql
    )
    assert 'patient_conditions.status = \'active\'' in medication_sql
    assert "row_number() OVER" in medication_sql
