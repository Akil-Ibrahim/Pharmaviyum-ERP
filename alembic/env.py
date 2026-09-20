"""
Alembic environment configuration with async SQLAlchemy support.

This enables Alembic to work with asyncpg and PostgreSQL + pgvector.
"""

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from src.pharmaviyum.db.base import Base
import src.pharmaviyum.models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    """Get a PostgreSQL URL suitable for Alembic's async engine."""
    url = os.getenv("PGVECTOR_DATABASE_URL")
    if not url:
        url = config.get_main_option("sqlalchemy.url")

    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql+asyncpg://"):
        return url
    return url


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
