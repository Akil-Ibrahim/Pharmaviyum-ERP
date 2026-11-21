"""Merge the pharmacy-domain cleanup branch into the production migration head.

Revision ID: 2026_09_19_000001
Revises: 2026_09_18_000003, 2026_09_16_000001
"""

from alembic import op

revision = "2026_09_19_000001"
down_revision = ("2026_09_18_000003", "2026_09_16_000001")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Merge migration branches without changing schema state."""
    pass


def downgrade() -> None:
    """Downgrade is intentionally unsupported across a merge-only revision."""
    raise RuntimeError(
        "Downgrade across the migration merge requires an explicit rollback plan"
    )
