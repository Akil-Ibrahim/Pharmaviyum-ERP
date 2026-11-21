"""Fixtures for integration tests using the CI PostgreSQL and Redis services."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from itertools import count

import pytest
from httpx import ASGITransport, AsyncClient
from redis import asyncio as aioredis
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.pharmaviyum.core.oauth2 import create_access_token
from src.pharmaviyum.database import Base
from src.pharmaviyum.main import app
from src.pharmaviyum.models.patients import Patient
from src.pharmaviyum.models.user import User
from src.pharmaviyum.shared.core.database import get_session

_phone_counter = count(100000000)


@pytest.fixture
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create an isolated engine against the CI PostgreSQL service."""
    from src.pharmaviyum.config import settings

    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )
    yield engine
    await engine.dispose()


@pytest.fixture
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create the test schema and yield a transactional session."""
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()

    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client with database access redirected to the test session."""

    async def override_get_session():
        yield test_db

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_session, None)


@pytest.fixture
async def authenticated_client(
    client: AsyncClient,
    test_db: AsyncSession,
) -> AsyncClient:
    """HTTP client authenticated as a test administrator."""
    user = User(
        id=1,
        email="test@example.com",
        username="test-admin",
        full_name="Test Admin",
        hashed_password="not-used-in-tests",
        is_active=True,
        is_superuser=True,
    )
    test_db.add(user)
    await test_db.flush()

    token = create_access_token(str(user.id))
    client.headers["Authorization"] = f"Bearer {token}"
    return client


class PatientFactory:
    """Small async factory that avoids adding a test-only factory dependency."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **overrides) -> Patient:
        index = next(_phone_counter)
        first_name = overrides.pop("first_name", "Test")
        last_name = overrides.pop("last_name", "Patient")
        patient = Patient(
            first_name=first_name,
            last_name=last_name,
            full_name=f"{first_name} {last_name}",
            phone=overrides.pop("phone", f"+38050{index:06d}"),
            country=overrides.pop("country", "UA"),
            **overrides,
        )
        self.session.add(patient)
        await self.session.flush()
        return patient


@pytest.fixture
def patient_factory(test_db: AsyncSession):
    """Return an async patient factory bound to the current test session."""
    return PatientFactory(test_db)


@pytest.fixture
def sample_patient_data():
    """Payload accepted by the patient create endpoint."""
    return {
        "first_name": "Ibrahim",
        "last_name": "Ibrahim",
        "phone": "+380501234567",
        "email": "ibragim@example.com",
        "country": "UA",
    }


@pytest.fixture
def sample_patient_update_data():
    """Payload accepted by the patient update endpoint."""
    return {
        "first_name": "Ibrahim",
        "loyalty_tier": "Gold",
    }


@pytest.fixture
async def test_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """Use Redis DB 15 so CI tests stay isolated from other Redis databases."""
    from src.pharmaviyum.config import settings

    base_url = settings.REDIS_URL.rsplit("/", 1)[0]
    redis = aioredis.from_url(
        f"{base_url}/15",
        encoding="utf-8",
        decode_responses=True,
    )
    await redis.flushdb()
    yield redis
    await redis.flushdb()
    await redis.aclose()
