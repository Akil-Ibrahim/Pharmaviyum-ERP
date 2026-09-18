"""Remove the legacy patient purchase aggregate.

Revision ID: 2026_09_18_000003
Revises: 2026_09_18_000002, 2026_09_15_000002
"""

from alembic import op
import sqlalchemy as sa


revision = "2026_09_18_000003"
down_revision = ("2026_09_18_000002", "2026_09_15_000002")
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("patients")}
    if "total_purchases" in columns:
        op.drop_column("patients", "total_purchases")


def downgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("patients")}
    if "total_purchases" not in columns:
        op.add_column(
            "patients",
            sa.Column("total_purchases", sa.Float(), nullable=False, server_default="0"),
        )
        op.execute(
            sa.text(
                """
                UPDATE patients p
                SET total_purchases = COALESCE(
                    (
                        SELECT SUM(pp.quantity * pp.unit_price)
                        FROM patient_purchases pp
                        WHERE pp.patient_id = p.id
                    ),
                    0
                )
                """
            )
        )
        op.alter_column("patients", "total_purchases", server_default=None)
