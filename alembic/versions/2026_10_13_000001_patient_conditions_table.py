"""Create the patient conditions table required by patient and dashboard workflows.

Revision ID: 2026_10_13_000001
Revises: 2026_10_08_000002
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_10_13_000001"
down_revision: Union[str, None] = "2026_10_08_000002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(bind: sa.Connection, name: str) -> bool:
    return sa.inspect(bind).has_table(name)


def upgrade() -> None:
    bind = op.get_bind()

    # Some deployed databases were created before this model had a migration.
    # Keep this migration safe to run against databases where the table exists.
    if _table_exists(bind, "patient_conditions"):
        return

    op.create_table(
        "patient_conditions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("condition_name", sa.String(length=200), nullable=False),
        sa.Column("icd10_code", sa.String(length=10), nullable=True),
        sa.Column(
            "severity",
            sa.String(length=30),
            nullable=False,
            server_default="moderate",
        ),
        sa.Column("diagnosis_date", sa.Date(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="active",
        ),
        sa.Column("treatment_notes", sa.Text(), nullable=True),
        sa.Column("current_medications", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "is_chronic",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_patient_conditions_patient_id",
        "patient_conditions",
        ["patient_id"],
    )
    op.create_index(
        "ix_patient_conditions_condition_name",
        "patient_conditions",
        ["condition_name"],
    )
    op.create_index(
        "ix_patient_conditions_icd10_code",
        "patient_conditions",
        ["icd10_code"],
    )
    op.create_index(
        "ix_patient_conditions_is_chronic",
        "patient_conditions",
        ["is_chronic"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    if _table_exists(bind, "patient_conditions"):
        op.drop_table("patient_conditions")
