"""Architecture boundary tests for the modular monolith."""

import inspect

import pytest

from src.pharmaviyum.application.ports.erp import ERPAdapter
from src.pharmaviyum.application.ports.repositories import PatientRepositoryPort
from src.pharmaviyum.core.tenancy import (
    get_current_tenant,
    get_optional_tenant,
    tenant_context,
)
from src.pharmaviyum.services.patient import PatientService


@pytest.mark.unit
def test_patient_service_depends_on_repository_port() -> None:
    parameter = inspect.signature(PatientService.__init__).parameters["repository"]
    assert parameter.annotation is PatientRepositoryPort


@pytest.mark.unit
def test_erp_adapter_is_application_port() -> None:
    assert getattr(ERPAdapter, "__module__") == "src.pharmaviyum.application.ports.erp"


@pytest.mark.unit
def test_tenant_context_is_scoped_and_fails_closed() -> None:
    assert get_optional_tenant() is None
    with pytest.raises(RuntimeError):
        get_current_tenant()

    with tenant_context("pharmacy-a"):
        assert get_current_tenant() == "pharmacy-a"
        with tenant_context("pharmacy-b"):
            assert get_current_tenant() == "pharmacy-b"
        assert get_current_tenant() == "pharmacy-a"

    assert get_optional_tenant() is None
