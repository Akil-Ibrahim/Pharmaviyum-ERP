"""SQL-level tenant predicate tests for order and purchase lookups."""

import pytest
from sqlalchemy.dialects import postgresql

from src.pharmaviyum.api.v1.orders import (
    _order_query,
    _patient_query,
    _purchase_query,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("statement", "expected_table"),
    [
        (_patient_query(19, 731), "patients"),
        (_order_query(23, 731), "orders"),
        (_purchase_query("ORDER-23", 731), "patient_purchases"),
    ],
)
def test_order_workflow_queries_apply_pharmacy_predicate(statement, expected_table):
    """Tenant scope must be part of SQL, not a post-fetch Python comparison."""
    compiled = statement.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": True},
    )
    sql = str(compiled)

    assert expected_table in sql
    assert "patients.pharmacy_id = 731" in sql


@pytest.mark.parametrize(
    "statement",
    [
        _patient_query(19, None),
        _order_query(23, None),
        _purchase_query("ORDER-23", None),
    ],
)
def test_global_superuser_queries_preserve_explicit_unscoped_semantics(statement):
    """A None scope retains the existing global-superuser query behavior."""
    compiled = statement.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": True},
    )
    sql = str(compiled)

    assert "pharmacy_id" not in sql
