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


# Account emails must never disclose the user's plaintext password.
def test_account_welcome_email_contains_only_password_setup_link() -> None:
    from src.pharmaviyum.modules.auth.utils import generate_new_account_email

    email = generate_new_account_email(
        email_to="pharmacist@example.test",
        username="pharmacist@example.test",
        setup_token="opaque-one-time-token",
    )

    assert "opaque-one-time-token" in email.html_content
    assert "Set Password" in email.html_content
    assert "Password:</strong>" not in email.html_content


def test_account_welcome_email_escapes_untrusted_username() -> None:
    from src.pharmaviyum.modules.auth.utils import generate_new_account_email

    email = generate_new_account_email(
        email_to="pharmacist@example.test",
        username='<img src=x onerror="alert(1)">',
        setup_token="opaque-one-time-token",
    )

    assert '<img src=x onerror="alert(1)">' not in email.html_content
    assert "&lt;img" in email.html_content
