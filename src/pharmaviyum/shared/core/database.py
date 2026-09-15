"""Compatibility exports for the canonical database infrastructure.

The application has one database owner: ``src.pharmaviyum.database``.
This module remains as a stable import boundary for the newer modular code
while the codebase is migrated away from the legacy ``shared.core`` path.
"""

from src.pharmaviyum.database import AsyncSessionLocal, Base, engine, get_db

# Backward-compatible names used by the modular auth/AI code.
async_session_factory = AsyncSessionLocal
get_session = get_db

__all__ = [
    "AsyncSessionLocal",
    "Base",
    "async_session_factory",
    "engine",
    "get_db",
    "get_session",
]
