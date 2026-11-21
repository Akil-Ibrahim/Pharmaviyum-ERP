"""Tests for Alembic's separation from application runtime credentials."""

import pytest

from src.pharmaviyum.db.migration_config import select_migration_database_url


@pytest.mark.unit
def test_migration_database_url_takes_precedence_over_runtime_url():
    assert (
        select_migration_database_url(
            {
                "ENVIRONMENT": "production",
                "DATABASE_URL": "postgresql+asyncpg://runtime@db/app",
                "MIGRATION_DATABASE_URL": "postgresql+asyncpg://migrator@db/app",
            }
        )
        == "postgresql+asyncpg://migrator@db/app"
    )


@pytest.mark.unit
def test_migration_test_url_takes_precedence_for_isolated_ci_database():
    assert (
        select_migration_database_url(
            {
                "ENVIRONMENT": "testing",
                "DATABASE_URL": "postgresql+asyncpg://runtime@db/app",
                "MIGRATION_TEST_DATABASE_URL": (
                    "postgresql+asyncpg://ci@localhost/test_db"
                ),
            }
        )
        == "postgresql+asyncpg://ci@localhost/test_db"
    )


@pytest.mark.unit
def test_production_refuses_to_fall_back_to_runtime_database_url():
    with pytest.raises(RuntimeError, match="MIGRATION_DATABASE_URL is required"):
        select_migration_database_url(
            {
                "ENVIRONMENT": "production",
                "DATABASE_URL": "postgresql+asyncpg://runtime@db/app",
            }
        )


@pytest.mark.unit
def test_staging_refuses_to_fall_back_to_runtime_database_url():
    with pytest.raises(RuntimeError, match="MIGRATION_DATABASE_URL is required"):
        select_migration_database_url(
            {
                "ENVIRONMENT": "staging",
                "DATABASE_URL": "postgresql+asyncpg://runtime@db/app",
            }
        )


@pytest.mark.unit
def test_local_development_keeps_database_url_compatibility():
    assert (
        select_migration_database_url(
            {
                "ENVIRONMENT": "development",
                "DATABASE_URL": "postgresql+asyncpg://local@localhost/dev",
            }
        )
        == "postgresql+asyncpg://local@localhost/dev"
    )


@pytest.mark.unit
def test_alembic_ini_url_remains_a_local_fallback():
    assert (
        select_migration_database_url({}, config_fallback="postgresql://localhost/dev")
        == "postgresql://localhost/dev"
    )


@pytest.mark.unit
def test_production_rejects_migration_test_url_as_a_substitute_for_migration_role():
    with pytest.raises(RuntimeError, match="MIGRATION_DATABASE_URL is required"):
        select_migration_database_url(
            {
                "ENVIRONMENT": "production",
                "DATABASE_URL": "postgresql+asyncpg://runtime@db/app",
                "MIGRATION_TEST_DATABASE_URL": "postgresql+asyncpg://ci@localhost/test_db",
            }
        )
