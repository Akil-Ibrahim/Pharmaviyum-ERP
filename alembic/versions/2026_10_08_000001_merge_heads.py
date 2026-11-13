"""Merge concurrent Alembic migration heads after the drug catalog and user metadata work."""

from typing import Sequence, Union

from alembic import op


revision: str = "2026_10_08_000001"
down_revision: Union[tuple[str, str], None] = (
    "2026_09_29_000001",
    "2026_10_05_000002",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
