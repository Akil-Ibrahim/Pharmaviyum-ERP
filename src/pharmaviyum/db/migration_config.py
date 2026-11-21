"""Select an Alembic URL without reusing production runtime credentials."""

from collections.abc import Mapping


def select_migration_database_url(
    environ: Mapping[str, str],
    *,
    config_fallback: str | None = None,
) -> str:
    """Select an explicit migration URL and fail closed in hosted environments."""
    environment = environ.get("ENVIRONMENT", "").strip().lower()

    migration_url = environ.get("MIGRATION_DATABASE_URL")
    if migration_url:
        return migration_url

    if environment in {"production", "staging"}:
        raise RuntimeError(
            "MIGRATION_DATABASE_URL is required in staging and production; "
            "Alembic must not use application runtime or test database credentials."
        )

    migration_test_url = environ.get("MIGRATION_TEST_DATABASE_URL")
    if migration_test_url:
        return migration_test_url

    fallback = (
        environ.get("DATABASE_URL")
        or environ.get("PGVECTOR_DATABASE_URL")
        or config_fallback
    )
    if not fallback:
        raise RuntimeError("No database URL is configured for Alembic.")
    return fallback
