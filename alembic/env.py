"""
Alembic environment configuration with async SQLAlchemy support.

Migrations use a dedicated credential in staging/production. Application
runtime credentials are never an implicit migration fallback in hosted
environments.
"""

import asyncio
import os
from logging.config import fileConfig
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from src.pharmaviyum.db.base import Base
from src.pharmaviyum.db.migration_config import select_migration_database_url
import src.pharmaviyum.models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    """Get a dedicated PostgreSQL URL suitable for Alembic's async engine."""
    url = select_migration_database_url(
        os.environ,
        config_fallback=config.get_main_option("sqlalchemy.url"),
    )

    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # asyncpg does not accept the channel_binding connection option.
    parts = urlsplit(url)
    query = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        normalized_key = key.lower()
        if normalized_key == "channel_binding":
            continue
        # asyncpg uses the "ssl" option, not libpq's "sslmode".
        if normalized_key == "sslmode":
            if not any(existing_key.lower() == "ssl" for existing_key, _ in query):
                query.append(("ssl", value))
            continue
        query.append((key, value))
    return urlunsplit(parts._replace(query=urlencode(query)))


def run_migrations_offline() -> None:
    """Run migrations without opening a database connection."""
    url = get_url().replace("+asyncpg", "")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against PostgreSQL using asyncpg."""
    url = get_url()

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=url,
    )

    async def run_async_migrations() -> None:
        async with connectable.connect() as connection:

            def do_run_migrations(sync_connection) -> None:
                context.configure(
                    connection=sync_connection,
                    target_metadata=target_metadata,
                )
                with context.begin_transaction():
                    context.run_migrations()

            await connection.run_sync(do_run_migrations)

    asyncio.run(run_async_migrations())
    asyncio.run(connectable.dispose())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
