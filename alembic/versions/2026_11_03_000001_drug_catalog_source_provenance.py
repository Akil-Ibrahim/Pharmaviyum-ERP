"""Add provenance and review metadata for external drug catalog records."""

from alembic import op
import sqlalchemy as sa


revision = "2026_11_03_000001"
down_revision = "2026_10_14_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "drug_catalog_source_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_name", sa.String(length=50), nullable=False),
        sa.Column("source_record_id", sa.String(length=150), nullable=False),
        sa.Column("source_version", sa.String(length=100), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("license_terms", sa.String(length=500), nullable=True),
        sa.Column("extracted_at", sa.DateTime(), nullable=False),
        sa.Column("normalized_payload", sa.JSON(), nullable=True),
        sa.Column(
            "review_status",
            sa.String(length=30),
            nullable=False,
            server_default="pending_review",
        ),
        sa.Column("match_confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("matched_drug_reference_id", sa.Integer(), nullable=True),
        sa.Column("matched_medicinal_product_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["matched_drug_reference_id"],
            ["drug_references.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["matched_medicinal_product_id"],
            ["medicinal_products.id"],
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint(
            "source_name",
            "source_record_id",
            "source_version",
            name="uq_drug_catalog_source_identity",
        ),
        sa.CheckConstraint(
            "review_status IN ('pending_review', 'approved', 'rejected', 'duplicate')",
            name="ck_drug_catalog_source_review_status",
        ),
        sa.CheckConstraint(
            "match_confidence IS NULL OR "
            "(match_confidence >= 0 AND match_confidence <= 1)",
            name="ck_drug_catalog_source_match_confidence",
        ),
        sa.CheckConstraint(
            "matched_drug_reference_id IS NULL OR "
            "matched_medicinal_product_id IS NULL",
            name="ck_drug_catalog_source_single_match_target",
        ),
    )
    op.create_index(
        "ix_drug_catalog_source_records_source_name",
        "drug_catalog_source_records",
        ["source_name"],
    )
    op.create_index(
        "ix_drug_catalog_source_records_review_status",
        "drug_catalog_source_records",
        ["review_status"],
    )
    op.create_index(
        "ix_drug_catalog_source_records_matched_drug_reference_id",
        "drug_catalog_source_records",
        ["matched_drug_reference_id"],
    )
    op.create_index(
        "ix_drug_catalog_source_records_matched_medicinal_product_id",
        "drug_catalog_source_records",
        ["matched_medicinal_product_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_drug_catalog_source_records_matched_medicinal_product_id",
        table_name="drug_catalog_source_records",
    )
    op.drop_index(
        "ix_drug_catalog_source_records_matched_drug_reference_id",
        table_name="drug_catalog_source_records",
    )
    op.drop_index(
        "ix_drug_catalog_source_records_review_status",
        table_name="drug_catalog_source_records",
    )
    op.drop_index(
        "ix_drug_catalog_source_records_source_name",
        table_name="drug_catalog_source_records",
    )
    op.drop_table("drug_catalog_source_records")
