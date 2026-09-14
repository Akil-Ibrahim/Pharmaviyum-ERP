"""
Alembic environment configuration with async SQLAlchemy support.

This enables Alembic to work with asyncpg and PostgreSQL + pgvector.
"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, text
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import asyncio
import os

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata for autogenerate support (optional)
target_metadata = None

# Get database URL from environment or config
def get_url():
    """Get database URL from environment variable or alembic.ini."""
    url = os.getenv("PGVECTOR_DATABASE_URL")
    if url:
        # Convert asyncpg URL to sync for Alembic offline mode
        return url.replace("+asyncpg", "")
    return config.get_main_option("sqlalchemy.url")


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    This configures the context with just a URL and not an Engine,
    so that actual DB access is not required.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode with async engine.
    
    Creates an Engine and associates a connection with the context.
    """
    url = get_url()
    
    # Create async engine
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=url,
    )

    async def run_async_migrations():
        """Execute migrations asynchronously."""
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)

    async def do_run_migrations(connection):
        """Run migrations on the given connection."""
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()

    # Run async migrations
    asyncio.run(run_async_migrations())
    
    # Close engine
    asyncio.run(connectable.dispose())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
