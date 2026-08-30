"""
Pytest configuration and shared fixtures.

Provides:
- Test database with automatic setup/teardown
- Transaction-based test isolation
- Factory functions for test data
"""
import random
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create single event loop for all async tests in session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine with all tables."""
    test_db_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/pharmaviyum_test"
    
    engine = create_async_engine(test_db_url, echo=False, pool_pre_ping=True)
    
    # Create all tables here when Base is ready:
    # from app.shared.core.database import Base
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Database session with automatic transaction rollback."""
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with session_factory() as session:
        await session.begin()
        try:
            yield session
        finally:
            await session.rollback()


@pytest.fixture
def patient_factory(db_session: AsyncSession):
    """Factory for creating test patients."""
    async def create_patient(**kwargs):
        defaults = {
            "first_name": "Test",
            "last_name": f"Patient_{random.randint(1000, 9999)}",
            "phone": f"+84{random.randint(100000000, 999999999)}",
            "country": "VN",
            "loyalty_tier": "Bronze",
            "is_active": True,
        }
        defaults.update(kwargs)
        return defaults
    
    return create_patient
