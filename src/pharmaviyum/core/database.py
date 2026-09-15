"""
Database configuration and session management
Uses SQLAlchemy 2.0 async with PostgreSQL + pgvector
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.pharmaviyum.core.config import settings

# Create async engine with pgvector support
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)


# Async session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""

    pass


async def get_db() -> AsyncSession:
    """
    Dependency for FastAPI endpoints
    Provides async database session with automatic cleanup
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
