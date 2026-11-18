"""Retained historical revision; destructive origin-based catalog purge is disabled.

The revision ID remains in the graph for databases that already recorded it.
"""


revision = "2026_11_05_000004"
down_revision = "2026_11_05_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """No-op: ADR-0008 prohibits destructive manufacturer/country catalog filtering.

    This revision identifier is retained because it is already part of the
    deployed Alembic history. Production has already applied the former cleanup;
    this edit does not restore records previously deleted there. Databases that
    have not applied this revision must not execute the former destructive purge.
    """
    pass


def downgrade() -> None:
    """The historical destructive cleanup cannot be reconstructed by downgrade."""
    pass
