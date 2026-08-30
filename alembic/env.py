"""
Alembic environment configuration for async SQLAlchemy
Best practice 2026: Full async support, environment variables, model autoloading
"""
import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine, async_engine_from_config

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.pharmaviyum.core.config import settings
from src.pharmaviyum.core.database import Base

# ============================================================================
# IMPORT ALL MODELS
# ============================================================================
# This is critical - all models must be imported so their tables are registered
# with Base.metadata before Alembic can detect them.

# Patients module
try:
    from src.pharmaviyum.models.patients.patient import Patient  # noqa: F401
    from src.pharmaviyum.models.patients.patient_allergy import PatientAllergy  # noqa: F401
    from src.pharmaviyum.models.patients.patient_condition import PatientCondition  # noqa: F401
    from src.pharmaviyum.models.patients.patient_insurance import PatientInsurance  # noqa: F401
    from src.pharmaviyum.models.patients.consultation import Consultation  # noqa: F401
except Exception:  # pragma: no cover - compatibility fallback for partially initialized repo
    pass

# Prescriptions module
try:
    from src.pharmaviyum.models.prescriptions.prescription import Prescription  # noqa: F401
    from src.pharmaviyum.models.prescriptions.prescription_item import PrescriptionItem  # noqa: F401
    from src.pharmaviyum.models.prescriptions.prescription_fill import PrescriptionFill  # noqa: F401
    from src.pharmaviyum.models.prescriptions.medication_reminder import MedicationReminder  # noqa: F401
except Exception:  # pragma: no cover - compatibility fallback for partially initialized repo
    pass

# ============================================================================
# ALEMBIC CONFIGURATION
# ============================================================================

config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url with environment variable
# This allows different URLs for dev/test/prod
database_url = os.getenv(
    "DATABASE_URL",
    settings.DATABASE_URL,
)
config.set_main_option("sqlalchemy.url", database_url)

# Target metadata for 'autogenerate' support
target_metadata = Base.metadata

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def include_object(object, name, type_, reflected, compare_to):
    """
    Filter objects to include/exclude from migration generation
    
    Useful for:
    - Excluding system tables (e.g., spatial_ref_sys)
    - Excluding views
    - Excluding specific tables managed externally
    """
    # Exclude tables managed by extensions
    if type_ == "table" and name in [
        "spatial_ref_sys",  # PostGIS
        "geography_columns",
        "geometry_columns",
    ]:
        return False
    
    return True


def process_revision_directives(context, revision, directives):
    """
    Process revision directives before writing migration file
    
    Useful for:
    - Removing empty migrations
    - Adding custom headers
    - Modifying migration operations
    """
    if config.cmd_opts.autogenerate:
        script = directives[0]
        if script.upgrade_ops.is_empty():
            # Don't create empty migration files
            directives[:] = []
            print("No changes detected - skipping migration generation")


# ============================================================================
# OFFLINE MIGRATION MODE
# ============================================================================

def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode
    
    Configures the context with just a URL, not an Engine.
    Useful for generating SQL scripts without connecting to database.
    
    Usage:
        alembic upgrade head --sql
    """
    url = config.get_main_option("sqlalchemy.url")
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        process_revision_directives=process_revision_directives,
        compare_type=True,  # Detect column type changes
        compare_server_default=True,  # Detect default value changes
    )
    
    with context.begin_transaction():
        context.run_migrations()


# ============================================================================
# ONLINE MIGRATION MODE (ASYNC)
# ============================================================================

def do_run_migrations(connection):
    """Run migrations with the given connection"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
        process_revision_directives=process_revision_directives,
        compare_type=True,
        compare_server_default=True,
    )
    
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in 'online' mode with async engine
    
    Creates an async Engine and associates a connection with the context.
    This is the main entry point for async migrations.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    
    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode
    
    Entry point for async migrations.
    """
    asyncio.run(run_async_migrations())


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
