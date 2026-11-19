"""Unit tests for transient PostgreSQL readiness retry classification."""

import pytest
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError

from src.pharmaviyum.core.db_readiness import (
    _is_transient_database_error as core_is_transient,
)
from src.pharmaviyum.shared.core.db_readiness import (
    _is_transient_database_error as shared_is_transient,
)


@pytest.mark.parametrize("classifier", [core_is_transient, shared_is_transient])
def test_operational_errors_are_retryable(classifier):
    error = OperationalError("SELECT 1", {}, Exception("connection refused"))

    assert classifier(error) is True


@pytest.mark.parametrize("classifier", [core_is_transient, shared_is_transient])
def test_invalidated_dbapi_connections_are_retryable(classifier):
    error = DBAPIError(
        "SELECT 1",
        {},
        Exception("connection lost"),
        connection_invalidated=True,
    )

    assert classifier(error) is True


@pytest.mark.parametrize("classifier", [core_is_transient, shared_is_transient])
def test_non_invalidating_dbapi_errors_are_not_retryable(classifier):
    error = DBAPIError("SELECT 1", {}, Exception("driver rejected operation"))

    assert classifier(error) is False


@pytest.mark.parametrize("classifier", [core_is_transient, shared_is_transient])
def test_integrity_errors_are_not_retryable(classifier):
    error = IntegrityError("INSERT", {}, Exception("constraint violation"))

    assert classifier(error) is False


@pytest.mark.parametrize("classifier", [core_is_transient, shared_is_transient])
def test_programming_errors_are_not_retryable(classifier):
    from sqlalchemy.exc import ProgrammingError

    error = ProgrammingError("SELECT invalid", {}, Exception("syntax error"))

    assert classifier(error) is False
