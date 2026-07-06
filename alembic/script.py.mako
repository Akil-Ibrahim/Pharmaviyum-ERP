"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# ============================================================================
# REVISION IDENTIFIERS
# ============================================================================

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


# ============================================================================
# UPGRADE FUNCTION
# ============================================================================

def upgrade() -> None:
    """
    Apply migration changes
    
    This function is called when upgrading the database schema.
    All operations should be idempotent and reversible.
    """
    ${upgrades if upgrades else "pass"}


# ============================================================================
# DOWNGRADE FUNCTION
# ============================================================================

def downgrade() -> None:
    """
    Revert migration changes
    
    This function is called when downgrading the database schema.
    Must exactly reverse the changes made in upgrade().
    
    WARNING: Downgrades may result in data loss!
    Always test downgrades in a staging environment first.
    """
    ${downgrades if downgrades else "pass"}
