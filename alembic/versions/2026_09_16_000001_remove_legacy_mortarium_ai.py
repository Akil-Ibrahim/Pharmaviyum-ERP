"""Remove the legacy Mortarium AI session table.

Revision ID: 2026_09_16_000001
Revises: 20260915_pharmacy_domain
"""

from alembic import op

revision = "2026_09_16_000001"
down_revision = "20260915_pharmacy_domain"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("mortarium_ai_sessions")


def downgrade() -> None:
    # The legacy model is intentionally removed from the application code.
    # Downgrade is unsupported because recreating it would restore deleted legacy state.
    raise RuntimeError("Legacy Mortarium AI state is intentionally not restorable")
