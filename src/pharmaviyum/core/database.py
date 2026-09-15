"""Compatibility exports for the canonical database infrastructure."""

from src.pharmaviyum.database import AsyncSessionLocal, Base, engine, get_db

async_session = AsyncSessionLocal

__all__ = ["AsyncSessionLocal", "Base", "async_session", "engine", "get_db"]
