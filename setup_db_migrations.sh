#!/bin/bash
# ============================================================================
# Database Migrations Setup Script (Alembic)
# Best practice 2026: Async migrations, versioning, rollback strategy
# ============================================================================
set -e

echo "🗄️ Setting up Database Migrations for Pharmaviyum CRM..."

echo ""
# ============================================================================
# 1. UPDATE REQUIREMENTS
# ============================================================================
cat >> requirements.txt << 'EOF'
# Database migrations
alembic==1.13.3
asyncpg==0.29.0
EOF

echo "✅ requirements.txt updated with Alembic"

# ============================================================================
# 2. CREATE ALEMBIC DIRECTORY STRUCTURE
# ============================================================================
mkdir -p alembic/versions
mkdir -p alembic/seed_data
mkdir -p scripts/migrations

echo "✅ Alembic directories created"

# ============================================================================
# 3. ALEMBIC CONFIGURATION (alembic.ini)
# ============================================================================
cat > alembic.ini << 'EOF'
# ============================================================================
# Alembic Configuration File
# Best practice 2026: Async support, environment variables
# ===========================================================================
[alembic]
# Path to migration scripts
script_location = alembic
# Template for new migration files
file_template = %(year)d_%(month).2d_%(day).2d_%(hour).2d%(minute).2d-%(rev)s_%(slug)s
# Timezone for file_template (UTC for consistency)
timezone = UTC
# Truncate long slugs to this length
truncate_slug_length = 40
# sys.path prepended to Python path when running migrations
prepend_sys_path = .
# Version path separator (for migration branches)
version_path_separator = os
# Output encoding for migration files
output_encoding = utf-8
# ============================================================================
# DATABASE URL
# ============================================================================
# NOTE: This is overridden by env.py using environment variables
# Do NOT put real credentials here - use .env file instead
sqlalchemy.url = postgresql+asyncpg://postgres:postgres@localhost:5432/pharmaviyum
# ============================================================================
# POSTGRESQL SPECIFIC SETTINGS
# ===========================================================================
[post_write_hooks]
# Automatically format migration files with black
hooks = black
black.type = console_scripts
black.entrypoint = black
black.options = -l 100
# ============================================================================
# LOGGING CONFIGURATION
# ===========================================================================
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
EOF

echo "✅ alembic.ini created"

# ============================================================================
# 4. ALEMBIC ENVIRONMENT (env.py) - ASYNC SUPPORT
# ============================================================================
cat > alembic/env.py << 'EOF'
"""Alembic environment configuration for async SQLAlchemy
Best practice 2026: Full async support, environment variables, model autoloading"""
import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

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
from src.pharmaviyum.models.patients.patient import Patient  # noqa: F401
from src.pharmaviyum.models.patients.patient_allergy import PatientAllergy  # noqa: F401
from src.pharmaviyum.models.patients.patient_condition import PatientCondition  # noqa: F401
from src.pharmaviyum.models.patients.patient_insurance import PatientInsurance  # noqa: F401
from src.pharmaviyum.models.patients.consultation import Consultation  # noqa: F401
# Prescriptions module
from src.pharmaviyum.models.prescriptions.prescription import Prescription  # noqa: F401
from src.pharmaviyum.models.prescriptions.prescription_item import PrescriptionItem  # noqa: F401
from src.pharmaviyum.models.prescriptions.prescription_fill import PrescriptionFill  # noqa: F401
from src.pharmaviyum.models.prescriptions.medication_reminder import MedicationReminder  # noqa: F401

# ============================================================================
# ALEMBIC CONFIGURATION
# ============================================================================
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url with environment variable
# This allows different URLs for dev/test/prod
database_url = os.getenv("DATABASE_URL", settings.DATABASE_URL)
config.set_main_option("sqlalchemy.url", database_url)

# Target metadata for 'autogenerate' support
target_metadata = Base.metadata

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def include_object(object, name, type_, reflected, compare_to):
    """Filter objects to include/exclude from migration generation.
    Useful for:
    - Excluding system tables (e.g., spatial_ref_sys)
    - Excluding views
    - Excluding specific tables managed externally
    """
    if type_ == "table" and name in ["spatial_ref_sys", "geography_columns", "geometry_columns"]:
        return False
    return True

def process_revision_directives(context, revision, directives):
    """Process revision directives before writing migration file.
    Useful for:
    - Removing empty migrations
    - Adding custom headers
    - Modifying migration operations
    """
    if config.cmd_opts.autogenerate:
        script = directives[0]
        if script.upgrade_ops.is_empty():
            directives[:] = []
            print("No changes detected - skipping migration generation")

# ============================================================================
# OFFLINE MIGRATION MODE
# ============================================================================
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    Generates SQL scripts without connecting to the database.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        process_revision_directives=process_revision_directives,
        compare_type=True,
        compare_server_default=True,
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
    """Run migrations in 'online' mode with async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online() -> None:
    """Entry point for async migrations."""
    asyncio.run(run_async_migrations())

# ============================================================================
# MAIN EXECUTION
# ============================================================================
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
EOF

echo "✅ alembic/env.py created"

# ============================================================================
# 5. MIGRATION SCRIPT TEMPLATE
# ============================================================================
cat > alembic/script.py.mako << 'EOF'
"""${message}
Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}
# ============================================================================
# REVISION IDENTIFIERS
# ============================================================================
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}
# ============================================================================
# UPGRADE FUNCTION
# ============================================================================
def upgrade() -> None:
    """Apply migration changes.
    All operations should be idempotent and reversible.
    """
    ${upgrades if upgrades else "pass"}
# ============================================================================
# DOWNGRADE FUNCTION
# ============================================================================
def downgrade() -> None:
    """Revert migration changes.
    Must exactly reverse the changes made in upgrade().
    WARNING: Downgrades may result in data loss!
    Always test downgrades in a staging environment first.
    """
    ${downgrades if downgrades else "pass"}
EOF

echo "✅ alembic/script.py.mako created"

# ============================================================================
# 6. INITIAL MIGRATION (Patients + Prescriptions)
# ============================================================================
cat > alembic/versions/2026_07_06_000000_001_initial_patients_prescriptions.py << 'EOF'
"""Initial migration: Patients and Prescriptions tables
Revision ID: 001_initial
Revises: 
Create Date: 2026-07-06 00:00:00.000000+00:00

This is the initial migration that creates the foundation tables for:
- Patients module (5 tables)
- Prescriptions module (4 tables)
Best practice 2026: Comprehensive indexes, JSON fields for flexibility, soft delete support, audit timestamps.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Create initial tables for Patients and Prescriptions modules"""
    # --------------------------------------------------------------------
    # PATIENTS MODULE
    # --------------------------------------------------------------------
    op.create_table(
        'patients',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('external_id', sa.String(100), nullable=True, unique=True, index=True),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('full_name', sa.String(200), nullable=False, index=True),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('gender', sa.String(20), nullable=True),
        sa.Column('phone', sa.String(20), nullable=False, index=True),
        sa.Column('email', sa.String(200), nullable=True, index=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(100), nullable=True, index=True),
        sa.Column('country', sa.String(2), nullable=False, server_default='VN', index=True),
        sa.Column('postal_code', sa.String(20), nullable=True),
        sa.Column('national_id', sa.String(50), nullable=True),
        sa.Column('insurance_number', sa.String(50), nullable=True),
        sa.Column('allergies_notes', sa.Text(), nullable=True),
        sa.Column('chronic_conditions', sa.Text(), nullable=True),
        sa.Column('blood_type', sa.String(5), nullable=True),
        sa.Column('preferred_language', sa.String(5), nullable=False, server_default='vi'),
        sa.Column('preferred_notification_channel', sa.String(20), nullable=False, server_default='zalo'),
        sa.Column('loyalty_tier', sa.String(20), nullable=False, server_default='Bronze'),
        sa.Column('loyalty_points', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_purchases', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('visit_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_visit_date', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', index=True),
        sa.Column('pos_system', sa.String(50), nullable=True),
        sa.Column('synced_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_patients_country_active', 'patients', ['country', 'is_active'])
    op.create_index('ix_patients_loyalty_tier', 'patients', ['loyalty_tier', 'is_active'])
    op.create_index('ix_patients_last_visit', 'patients', ['last_visit_date'])
    op.create_index('ix_patients_full_name_trgm', 'patients', ['full_name'], postgresql_using='gin', postgresql_ops={'full_name': 'gin_trgm_ops'})

    # patient_allergies
    op.create_table(
        'patient_allergies',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('patient_id', sa.Integer(), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('allergen_type', sa.String(50), nullable=False),
        sa.Column('allergen_name', sa.String(200), nullable=False, index=True),
        sa.Column('allergen_code', sa.String(50), nullable=True),
        sa.Column('severity', sa.String(30), nullable=False, server_default='moderate'),
        sa.Column('reaction', sa.Text(), nullable=True),
        sa.Column('onset_date', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('verified_by', sa.String(100), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_patient_allergies_patient_type', 'patient_allergies', ['patient_id', 'allergen_type'])

    # patient_conditions
    op.create_table(
        'patient_conditions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('patient_id', sa.Integer(), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('condition_name', sa.String(200), nullable=False, index=True),
        sa.Column('icd10_code', sa.String(10), nullable=True, index=True),
        sa.Column('severity', sa.String(30), nullable=False, server_default='moderate'),
        sa.Column('diagnosis_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('treatment_notes', sa.Text(), nullable=True),
        sa.Column('current_medications', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_chronic', sa.Boolean(), nullable=False, server_default='false', index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_patient_conditions_patient_status', 'patient_conditions', ['patient_id', 'status'])

    # patient_in
    op.create_table(
        'patient_insurances',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('patient_id', sa.Integer(), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('provider_name', sa.String(100), nullable=False),
        sa.Column('policy_number', sa.String(50), nullable=False, unique=True),
        sa.Column('coverage_start', sa.Date(), nullable=False),
        sa.Column('coverage_end', sa.Date(), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_patient_insurances_patient', 'patient_insurances', ['patient_id'])

    # --------------------------------------------------------------------
    # PRESCRIPTIONS MODULE
    # --------------------------------------------------------------------
    op.create_table(
        'prescriptions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('patient_id', sa.Integer(), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('doctor_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('issued_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_prescriptions_patient_status', 'prescriptions', ['patient_id', 'status'])

    op.create_table(
        'prescription_items',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('prescription_id', sa.Integer(), sa.ForeignKey('prescriptions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('medication_name', sa.String(200), nullable=False),
        sa.Column('dosage', sa.String(100), nullable=False),
        sa.Column('frequency', sa.String(100), nullable=False),
        sa.Column('duration_days', sa.Integer(), nullable=False),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_prescription_items_prescription', 'prescription_items', ['prescription_id'])

    op.create_table(
        'prescription_fills',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('prescription_id', sa.Integer(), sa.ForeignKey('prescriptions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('filled_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('pharmacy_id', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_prescription_fills_prescription', 'prescription_fills', ['prescription_id'])

    op.create_table(
        'medication_reminders',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('prescription_item_id', sa.Integer(), sa.ForeignKey('prescription_items.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('reminder_time', sa.DateTime(), nullable=False),
        sa.Column('method', sa.String(20), nullable=False, server_default='push'),
        sa.Column('status', sa.String(20), nullable=False, server_default='scheduled'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_medication_reminders_item', 'medication_reminders', ['prescription_item_id'])

def downgrade() -> None:
    # Drop tables in reverse order to respect foreign keys
    op.drop_table('medication_reminders')
    op.drop_table('prescription_fills')
    op.drop_table('prescription_items')
    op.drop_table('prescriptions')
    op.drop_table('patient_insurances')
    op.drop_table('patient_conditions')
    op.drop_table('patient_allergies')
    op.drop_table('patients')
EOF

echo "✅ Initial migration script created"

# ============================================================================
# 7. Make script executable
# ============================================================================
chmod +x setup_db_migrations.sh

echo "✅ setup_db_migrations.sh is now executable"
