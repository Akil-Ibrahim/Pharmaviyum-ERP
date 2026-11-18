"""Add regulatory reference tables for medical devices.

Revision ID: 2026_11_16_000004
Revises: 2026_11_16_000003
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_11_16_000004"
down_revision: Union[str, None] = "2026_11_16_000003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "medical_devices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("source_record_id", sa.String(length=160), nullable=False),
        sa.Column("source_version", sa.String(length=160), nullable=True),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("license_terms", sa.String(length=1000), nullable=True),
        sa.Column("country", sa.String(length=2), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("brand_name", sa.String(length=200), nullable=True),
        sa.Column("model", sa.String(length=200), nullable=True),
        sa.Column("manufacturer", sa.String(length=250), nullable=True),
        sa.Column("manufacturer_country", sa.String(length=100), nullable=True),
        sa.Column("device_type", sa.String(length=120), nullable=True),
        sa.Column("risk_class", sa.String(length=40), nullable=True),
        sa.Column("intended_purpose", sa.String(length=1000), nullable=True),
        sa.Column("regulatory_status", sa.String(length=80), nullable=True),
        sa.Column("source_updated_at", sa.Date(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("imported_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "source_name",
            "source_record_id",
            name="uq_medical_device_source_record",
        ),
    )
    for column in ("source_name", "country", "name", "brand_name", "manufacturer", "risk_class"):
        op.create_index(
            f"ix_medical_devices_{column}",
            "medical_devices",
            [column],
        )

    op.create_table(
        "medical_device_identifiers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "medical_device_id",
            sa.Integer(),
            sa.ForeignKey("medical_devices.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("identifier_type", sa.String(length=60), nullable=False),
        sa.Column("identifier_value", sa.String(length=160), nullable=False),
        sa.Column("issuing_agency", sa.String(length=40), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.UniqueConstraint(
            "medical_device_id",
            "identifier_type",
            "identifier_value",
            name="uq_medical_device_identifier",
        ),
    )
    op.create_index(
        "ix_medical_device_identifiers_medical_device_id",
        "medical_device_identifiers",
        ["medical_device_id"],
    )
    op.create_index(
        "ix_medical_device_identifiers_identifier_value",
        "medical_device_identifiers",
        ["identifier_value"],
    )

    op.create_table(
        "medical_device_authorizations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "medical_device_id",
            sa.Integer(),
            sa.ForeignKey("medical_devices.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("country", sa.String(length=2), nullable=False),
        sa.Column("authorization_id", sa.String(length=120), nullable=False),
        sa.Column("authorization_type", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=80), nullable=True),
        sa.Column("risk_class", sa.String(length=40), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("source_updated_at", sa.Date(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.UniqueConstraint(
            "medical_device_id",
            "country",
            "authorization_id",
            name="uq_medical_device_authorization",
        ),
    )
    op.create_index(
        "ix_medical_device_authorizations_medical_device_id",
        "medical_device_authorizations",
        ["medical_device_id"],
    )
    op.create_index(
        "ix_medical_device_authorizations_country",
        "medical_device_authorizations",
        ["country"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_medical_device_authorizations_country",
        table_name="medical_device_authorizations",
    )
    op.drop_index(
        "ix_medical_device_authorizations_medical_device_id",
        table_name="medical_device_authorizations",
    )
    op.drop_table("medical_device_authorizations")
    op.drop_index(
        "ix_medical_device_identifiers_identifier_value",
        table_name="medical_device_identifiers",
    )
    op.drop_index(
        "ix_medical_device_identifiers_medical_device_id",
        table_name="medical_device_identifiers",
    )
    op.drop_table("medical_device_identifiers")
    for column in ("source_name", "country", "name", "brand_name", "manufacturer", "risk_class"):
        op.drop_index(
            f"ix_medical_devices_{column}",
            table_name="medical_devices",
        )
    op.drop_table("medical_devices")
