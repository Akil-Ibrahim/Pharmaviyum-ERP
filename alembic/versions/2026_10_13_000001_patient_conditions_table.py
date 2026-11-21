"""Ensure the patient conditions table exists for patient and dashboard workflows.

Revision ID: 2026_10_13_000001
Revises: 2026_10_08_000002

This is intentionally idempotent: multiple Render services may run Alembic
against the same database during a rollout. Downgrade is a no-op so an
existing table and its patient data are never dropped by rollback.
"""

from typing import Sequence, Union

from alembic import op


revision: str = "2026_10_13_000001"
down_revision: Union[str, None] = "2026_10_08_000002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use IF NOT EXISTS to avoid a race when both Render services start at
    # once and run migrations against the same database.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS patient_conditions (
            id SERIAL PRIMARY KEY,
            patient_id INTEGER NOT NULL
                REFERENCES patients(id) ON DELETE CASCADE,
            condition_name VARCHAR(200) NOT NULL,
            icd10_code VARCHAR(10),
            severity VARCHAR(30) NOT NULL DEFAULT 'moderate',
            diagnosis_date DATE,
            status VARCHAR(20) NOT NULL DEFAULT 'active',
            treatment_notes TEXT,
            current_medications TEXT,
            notes TEXT,
            is_chronic BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_patient_conditions_patient_id "
        "ON patient_conditions (patient_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_patient_conditions_condition_name "
        "ON patient_conditions (condition_name)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_patient_conditions_icd10_code "
        "ON patient_conditions (icd10_code)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_patient_conditions_is_chronic "
        "ON patient_conditions (is_chronic)"
    )


def downgrade() -> None:
    # Preserve patient condition data. This migration may have found a table
    # that existed before the migration was introduced.
    pass
