"""Pytest configuration and fixtures for async tests using sqlite+aiosqlite."""

import asyncio
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker


# Use an async sqlite DB for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_async.db"


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def engine():
    engine = create_async_engine(TEST_DATABASE_URL, future=True, echo=False)

    # create tables
    from src.pharmaviyum.db.base import Base

    async def _create():
        async with engine.begin() as conn:
            # import models so they are registered with Base
            import src.pharmaviyum.models.user  # noqa: F401
            import src.pharmaviyum.models.product  # noqa: F401
            import src.pharmaviyum.models.order  # noqa: F401
            import src.pharmaviyum.models.client  # noqa: F401
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create())

    yield engine

    asyncio.run(engine.dispose())


@pytest.fixture
async def db_session(engine):
    async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture
def client(engine):
    """Create test client and override DB dependency with async test session."""
    from src.pharmaviyum.main import app
    import src.pharmaviyum.db.session as db_session_module

    async def _override_get_db():
        async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            yield session

    # Override the async get_db used by API modules
    app.dependency_overrides[db_session_module.get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
