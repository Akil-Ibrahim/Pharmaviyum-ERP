"""Compatibility exports for the canonical database infrastructure."""

from src.pharmaviyum.database import AsyncSessionLocal, Base, engine, get_db

async_session = AsyncSessionLocal
async_session_factory = AsyncSessionLocal

__all__ = [
    "AsyncSessionLocal",
    "Base",
    "async_session",
    "async_session_factory",
    "engine",
    "get_db",
]
