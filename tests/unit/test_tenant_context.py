import pytest

from src.pharmaviyum.shared.tenant import get_tenant, require_tenant, tenant_scope


def test_tenant_scope_is_request_scoped() -> None:
    assert get_tenant() is None

    with tenant_scope(42) as tenant:
        assert tenant.pharmacy_id == 42
        assert get_tenant() == tenant
        assert require_tenant() == tenant

    assert get_tenant() is None


def test_tenant_scope_restores_nested_context() -> None:
    with tenant_scope(1):
        assert require_tenant().pharmacy_id == 1
        with tenant_scope(2):
            assert require_tenant().pharmacy_id == 2
        assert require_tenant().pharmacy_id == 1


def test_tenant_context_rejects_invalid_pharmacy_id() -> None:
    with pytest.raises(ValueError, match="pharmacy_id"):
        with tenant_scope(0):
            pass


def test_require_tenant_fails_closed() -> None:
    with pytest.raises(RuntimeError, match="Tenant context is required"):
        require_tenant()
