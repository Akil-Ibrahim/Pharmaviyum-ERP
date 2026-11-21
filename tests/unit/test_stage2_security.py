import pytest

from src.pharmaviyum.api.v1.pharmacy_entities import router


@pytest.mark.unit
def test_sensitive_stage2_routes_require_superuser() -> None:
    protected_paths = {
        "/api/v1/prescriptions": {"GET", "POST"},
        "/api/v1/erp/integrations": {"GET", "POST"},
        "/api/v1/erp/integrations/{integration_id}/events": {"GET", "POST"},
    }

    routes_by_path = {}
    for route in router.routes:
        expected_methods = protected_paths.get(route.path)
        if expected_methods is None:
            continue
        routes_by_path.setdefault(route.path, set()).update(route.methods or ())
        dependency_names = {
            getattr(dependency.call, "__name__", "")
            for dependency in route.dependant.dependencies
        }
        assert "get_current_active_superuser" in dependency_names

    for path, expected_methods in protected_paths.items():
        assert expected_methods <= routes_by_path.get(path, set())


@pytest.mark.unit
def test_inventory_mutations_require_superuser() -> None:
    protected_paths = {
        ("/api/v1/inventory", "POST"),
        ("/api/v1/inventory/{inventory_id}", "PATCH"),
        ("/api/v1/inventory/{inventory_id}", "DELETE"),
    }

    for route in router.routes:
        for method in route.methods or ():
            if (route.path, method) not in protected_paths:
                continue
            dependency_names = {
                getattr(dependency.call, "__name__", "")
                for dependency in route.dependant.dependencies
            }
            assert "get_current_active_superuser" in dependency_names
