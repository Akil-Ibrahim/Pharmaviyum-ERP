"""
Global pytest fixtures
Best practice 2026: Comprehensive test setup with database isolation
"""
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from redis import asyncio as aioredis
from httpx import AsyncClient, ASGITransport
from src.pharmaviyum.core.database import Base
from src.pharmaviyum.main import app
from src.pharmaviyum.core.config import settings


# ============================================================================
# EVENT LOOP
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    # Use separate test database
    test_db_url = settings.DATABASE_URL.replace("pharmaviyum", "pharmaviyum_test")
    
    engine = create_async_engine(
        test_db_url,
        echo=False,
        pool_pre_ping=True,
    )
    
    yield engine
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create test database session with rollback
    
    Each test gets a fresh database state.
    All changes are rolled back after test.
    """
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_factory() as session:
        yield session
        
        # Rollback all changes
        await session.rollback()
    
    # Drop all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(test_db: AsyncSession) -> AsyncSession:
    """Alias for test_db for convenience"""
    return test_db


# ============================================================================
# REDIS FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
async def test_redis():
    """Create test Redis connection"""
    # Use separate Redis DB for tests
    test_redis_url = settings.REDIS_URL.rstrip("/").rsplit("/", 1)[0] + "/15"
    
    redis = aioredis.from_url(
        test_redis_url,
        encoding="utf-8",
        decode_responses=True,
    )
    
    # Flush test database
    await redis.flushdb()
    
    yield redis
    
    # Cleanup
    await redis.flushdb()
    await redis.close()


@pytest.fixture
async def redis_client(test_redis) -> aioredis.Redis:
    """Alias for test_redis"""
    return test_redis


# ============================================================================
# HTTP CLIENT FIXTURES
# ============================================================================

@pytest.fixture
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create async HTTP client for testing
    
    Overrides database dependency to use test database.
    """
    # Override database dependency
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[
        __import__("src.pharmaviyum.core.database", fromlist=["get_db"]).get_db
    ] = override_get_db
    
    # Create client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    
    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
async def authenticated_client(client: AsyncClient, test_db: AsyncSession) -> AsyncClient:
    """
    Create authenticated HTTP client
    
    Adds authentication headers to all requests.
    """
    from src.pharmaviyum.core.security import create_access_token
    
    # Create test user token
    token = create_access_token(
        data={
            "sub": "1",
            "email": "test@example.com",
            "role": "admin",
            "is_active": True,
        }
    )
    
    client.headers["Authorization"] = f"Bearer {token}"
    
    return client


# ============================================================================
# FACTORY FIXTURES
# ============================================================================

@pytest.fixture
def patient_factory(test_db: AsyncSession):
    """Patient factory with test database session"""
    from tests.factories import PatientFactory
    
    PatientFactory._meta.sqlalchemy_session = test_db
    
    return PatientFactory


@pytest.fixture
def patient_allergy_factory(test_db: AsyncSession):
    """Patient allergy factory"""
    from tests.factories import PatientAllergyFactory
    
    PatientAllergyFactory._meta.sqlalchemy_session = test_db
    
    return PatientAllergyFactory


@pytest.fixture
def patient_condition_factory(test_db: AsyncSession):
    """Patient condition factory"""
    from tests.factories import PatientConditionFactory
    
    PatientConditionFactory._meta.sqlalchemy_session = test_db
    
    return PatientConditionFactory


# ============================================================================
# MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_cache_service(mocker):
    """Mock cache service"""
    mock = mocker.AsyncMock()
    mock.get = mocker.AsyncMock(return_value=None)
    mock.set = mocker.AsyncMock(return_value=True)
    mock.delete = mocker.AsyncMock(return_value=True)
    
    mocker.patch(
        "src.pharmaviyum.services.patient.cache_service",
        mock,
    )
    
    return mock


@pytest.fixture
def mock_event_bus(mocker):
    """Mock event bus"""
    mock = mocker.AsyncMock()
    mock.emit = mocker.AsyncMock()
    
    mocker.patch(
        "src.pharmaviyum.services.patient.event_bus",
        mock,
    )
    
    return mock


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def sample_patient_data():
    """Sample patient creation data"""
    return {
        "first_name": "Ibrahim",
        "last_name": "Тестов",
        "phone": "+84123456789",
        "email": "ibragim@example.com",
        "country": "VN",
        "preferred_language": "vi",
    }


@pytest.fixture
def sample_patient_update_data():
    """Sample patient update data"""
    return {
        "first_name": "Новое имя",
        "loyalty_tier": "Gold",
    }
