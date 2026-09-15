"""Consolidate pharmacy people into patients and relink orders.

Revision ID: 2026_09_15_000001
Revises:
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "2026_09_15_000001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(bind: sa.Connection, name: str) -> bool:
    return sa.inspect(bind).has_table(name)


def upgrade() -> None:
    bind = op.get_bind()

    if not _table_exists(bind, "patients"):
        op.create_table(
            "patients",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("external_id", sa.String(100), nullable=True),
            sa.Column("first_name", sa.String(100), nullable=False),
            sa.Column("last_name", sa.String(100), nullable=False),
            sa.Column("full_name", sa.String(200), nullable=False),
            sa.Column("date_of_birth", sa.Date(), nullable=True),
            sa.Column("gender", sa.String(20), nullable=True),
            sa.Column("phone", sa.String(20), nullable=False),
            sa.Column("email", sa.String(200), nullable=True),
            sa.Column("address", sa.Text(), nullable=True),
            sa.Column("city", sa.String(100), nullable=True),
            sa.Column("country", sa.String(2), nullable=False, server_default="VN"),
            sa.Column("postal_code", sa.String(20), nullable=True),
            sa.Column("national_id", sa.String(50), nullable=True),
            sa.Column("insurance_number", sa.String(50), nullable=True),
            sa.Column("allergies_notes", sa.Text(), nullable=True),
            sa.Column("chronic_conditions", sa.Text(), nullable=True),
            sa.Column("blood_type", sa.String(5), nullable=True),
            sa.Column("preferred_language", sa.String(5), nullable=False, server_default="vi"),
            sa.Column(
                "preferred_notification_channel",
                sa.String(20),
                nullable=False,
                server_default="zalo",
            ),
            sa.Column("loyalty_tier", sa.String(20), nullable=False, server_default="Bronze"),
            sa.Column("loyalty_points", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_purchases", sa.Float(), nullable=False, server_default="0"),
            sa.Column("visit_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("last_visit_date", sa.DateTime(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("pos_system", sa.String(50), nullable=True),
            sa.Column("synced_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_patients_external_id", "patients", ["external_id"], unique=True)
        op.create_index("ix_patients_full_name", "patients", ["full_name"])
        op.create_index("ix_patients_phone", "patients", ["phone"], unique=True)
        op.create_index("ix_patients_email", "patients", ["email"])
        op.create_index("ix_patients_city", "patients", ["city"])
        op.create_index("ix_patients_country", "patients", ["country"])
        op.create_index("ix_patients_is_active", "patients", ["is_active"])

    if _table_exists(bind, "clients"):
        bind.execute(
            sa.text(
                """
                INSERT INTO patients (
                    external_id, first_name, last_name, full_name, date_of_birth,
                    phone, email, address, country, loyalty_tier, loyalty_points,
                    total_purchases, is_active, created_at, updated_at
                )
                SELECT
                    'legacy-client:' || c.id,
                    split_part(c.full_name, ' ', 1),
                    CASE
                        WHEN position(' ' IN c.full_name) > 0
                        THEN substring(c.full_name FROM position(' ' IN c.full_name) + 1)
                        ELSE split_part(c.full_name, ' ', 1)
                    END,
                    c.full_name,
                    c.birth_date::date,
                    c.phone,
                    c.email,
                    c.address,
                    'VN',
                    CASE WHEN c.discount_percent >= 20 THEN 'Gold' ELSE 'Bronze' END,
                    0,
                    COALESCE(c.total_spent, 0),
                    COALESCE(c.is_active, true),
                    COALESCE(c.created_at, now()),
                    COALESCE(c.updated_at, now())
                FROM clients c
                WHERE NOT EXISTS (
                    SELECT 1 FROM patients p WHERE p.external_id = 'legacy-client:' || c.id
                )
                ON CONFLICT (phone) DO NOTHING
                """
            )
        )

    if _table_exists(bind, "orders"):
        columns = {column["name"] for column in sa.inspect(bind).get_columns("orders")}
        if "patient_id" not in columns:
            op.add_column("orders", sa.Column("patient_id", sa.Integer(), nullable=True))
            op.create_index("ix_orders_patient_id", "orders", ["patient_id"])

        if "client_id" in columns and _table_exists(bind, "clients"):
            bind.execute(
                sa.text(
                    """
                    UPDATE orders o
                    SET patient_id = p.id
                    FROM clients c
                    JOIN patients p ON p.external_id = 'legacy-client:' || c.id
                    WHERE o.client_id = c.id AND o.patient_id IS NULL
                    """
                )
            )

        missing = bind.execute(
            sa.text("SELECT count(*) FROM orders WHERE patient_id IS NULL")
        ).scalar_one()
        if missing:
            raise RuntimeError(
                f"Cannot make orders.patient_id required: {missing} orders have no patient mapping"
            )

        op.alter_column("orders", "patient_id", nullable=False)
        if "client_id" in columns:
            op.drop_constraint("orders_client_id_fkey", "orders", type_="foreignkey")
            op.drop_index("ix_orders_client_id", table_name="orders", if_exists=True)
            op.drop_column("orders", "client_id")
        op.create_foreign_key(
            "orders_patient_id_fkey",
            "orders",
            "patients",
            ["patient_id"],
            ["id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    if _table_exists(bind, "orders"):
        columns = {column["name"] for column in sa.inspect(bind).get_columns("orders")}
        if "patient_id" in columns:
            raise RuntimeError(
                "Downgrade is intentionally blocked: restoring client_id would require an explicit, reviewed data migration."
            )
