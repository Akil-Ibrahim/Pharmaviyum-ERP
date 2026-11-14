"""Regression tests for authentication routes exposed by the active FastAPI app."""

from src.pharmaviyum.main import app


def test_password_recovery_routes_are_registered_in_active_api() -> None:
    """The active frontend must reach recovery and reset endpoints."""
    paths = app.openapi()["paths"]

    assert "/api/v1/auth/password-recovery/{email}" in paths
    assert "post" in paths["/api/v1/auth/password-recovery/{email}"]
    assert "/api/v1/auth/reset-password/" in paths
    assert "post" in paths["/api/v1/auth/reset-password/"]


def test_modular_auth_routes_do_not_gain_a_duplicate_api_prefix() -> None:
    """Router aggregation must not publish accidental /api/v1/api/v1 paths."""
    paths = app.openapi()["paths"]

    assert not any(path.startswith("/api/v1/api/v1/auth/") for path in paths)
