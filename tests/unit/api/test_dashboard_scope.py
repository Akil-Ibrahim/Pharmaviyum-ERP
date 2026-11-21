"""Regression tests for Dashboard tenant query scoping."""

import re
from datetime import datetime
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
            today_sales=0,
            month_revenue=0,
            month_orders=0,
            month_completed_orders=0,
            month_prescriptions=0,
            active_patients=0,
            retail_value=0,
            items=0,
            low_stock=0,
            stockout_items=0,
            near_expiry_value=0,
        )

    def scalar_one(self):
        return 0


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

    # PostgreSQL can resolve GROUP BY "category" to an underlying column
    # instead of the SELECT alias. Group by the full CASE expression to keep
    # prescription_required valid in the aggregate query.
    sales_category_sql = next(
        sql
        for sql in patient_queries
        if "AS category" in sql and "prescription_required" in sql
    )
    assert "GROUP BY CASE WHEN" in sales_category_sql
    assert "GROUP BY category" not in sales_category_sql

    # Inventory aggregates must constrain Inventory directly. Top-products
    # stock is pre-aggregated and joined rather than correlated per product.
    inventory_queries = [sql for sql in sql_statements if "inventory" in sql]
    assert inventory_queries
    assert all("pharmacy_id = " in sql for sql in inventory_queries)
    top_products_sql = next(
        sql
        for sql in sql_statements
        if "LIMIT" in sql and "patient_purchases.dispensed_packs" in sql
    )
    assert "GROUP BY inventory.product_id" in top_products_sql

    # The resolved tenant value must be bound to the same SQL predicate rather
    # than merely mentioning a pharmacy column.
    patient_params = [
        statement.compile(dialect=postgresql.dialect()).params
        for statement in session.statements
        if "patient_purchases" in str(statement.compile(dialect=postgresql.dialect()))
    ]
    assert all(42 in params.values() for params in patient_params)

    inventory_params = [
        statement.compile(dialect=postgresql.dialect()).params
        for statement in session.statements
        if "inventory" in str(statement.compile(dialect=postgresql.dialect()))
    ]
    assert all(42 in params.values() for params in inventory_params)

    # KPI aggregates are captured as execute() statements so multiple
    # metrics share one database round trip.
    assert any(
        "patients.pharmacy_id" in sql
        for sql in sql_statements
        if "today_sales" in sql or "month_orders" in sql
    )
    assert any(
        "inventory.pharmacy_id" in sql
        for sql in sql_statements
        if "retail_value" in sql or "low_stock" in sql
    )


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
    all_sql = sql_statements
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

    medication_statement = next(
        statement
        for statement in session.statements
        if "patient_conditions" in str(statement)
    )
    medication_compiled = medication_statement.compile(dialect=postgresql.dialect())
    medication_sql = str(medication_compiled)
    assert "patient_conditions.status =" in medication_sql
    assert "active" in medication_compiled.params.values()
    assert "row_number() OVER" in medication_sql
    assert "LIMIT %(param_" in medication_sql
    assert "patients.pharmacy_id =" in medication_sql


@pytest.mark.asyncio
async def test_dashboard_expiry_policy_keeps_three_buckets_disjoint():
    """Expiry SQL must implement expired/<=3m red, 3-12m yellow, >12m green."""
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

    expiry_statement = next(
        statement
        for statement in session.statements
        if "extended_warning" in str(statement) and "date_trunc" in str(statement)
    )
    compiled = expiry_statement.compile(dialect=postgresql.dialect())
    expiry_sql = str(
        expiry_statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )

    assert re.search(r"date_trunc\([^)]*expires_at\)\s*<", expiry_sql)
    assert re.search(r"date_trunc\([^)]*expires_at\)\s*>= ", expiry_sql)
    assert re.search(r"date_trunc\([^)]*expires_at\)\s*<= ", expiry_sql)
    assert re.search(r"date_trunc\([^)]*expires_at\)\s*> ", expiry_sql)
    assert "extended_warning" in expiry_sql

    cutoff_values = [
        value for value in compiled.params.values() if isinstance(value, datetime)
    ]
    assert len(set(cutoff_values)) >= 3
