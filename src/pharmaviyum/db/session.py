import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Async DB engine and session for FastAPI
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:pass@localhost:5432/pharmaviyum")

engine = create_async_engine(DATABASE_URL, future=True, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    """Async dependency that yields an `AsyncSession` and ensures close."""
    async with AsyncSessionLocal() as session:
        yield session

