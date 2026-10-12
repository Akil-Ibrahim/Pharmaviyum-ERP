#!/bin/bash
# ============================================================================
# Testing Infrastructure Setup Script
# ============================================================================
# This script sets up the testing environment for the Pharmaviyum CRM project.
# It creates configuration files, test directories, factories, fixtures, and
# example test cases, then updates the CI workflow and documentation.
# All comments are in English as requested.

set -e

echo "🧪 Setting up Testing Infrastructure for Pharmaviyum CRM..."

echo "=========================================================================="
# 1. Pytest configuration (pytest.ini)
cat > pytest.ini << 'EOF'
[pytest]
# Test discovery
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
# Async support
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
# Output options
addopts = \
    -v \
    --tb=short \
    --strict-markers \
    --strict-config \
    --cov=src/pharmaviyum \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    --cov-report=xml:coverage.xml \
    --cov-fail-under=80 \
    -x
# Markers for categorising tests
markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (database, redis)
    e2e: End-to-end tests (full stack)
    slow: Slow running tests
    external: Tests requiring external services
    smoke: Quick validation tests
# Filter warnings
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
# Logging configuration
log_cli = true
log_cli_level = INFO
log_format = %(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)
log_date_format = %Y-%m-%d %H:%M:%S
EOF

echo "✅ pytest.ini created"

# 2. Coverage configuration (.coveragerc)
cat > .coveragerc << 'EOF'
[run]
source = src/pharmaviyum
branch = True
parallel = True
concurrency = asyncio,thread
omit =
    */tests/*
    */migrations/*
    */__init__.py
    */main.py
    src/pharmaviyum/workers/worker.py
[report]
exclude_lines =
    pragma: no cover
    def __repr__
    if self.debug
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:    
    if TYPE_CHECKING:
    @abstractmethod
    raise ImportError
    pass
ignore_errors = True
show_missing = True
skip_covered = True
[html]
# HTML coverage report directory
directory = htmlcov
title = Pharmaviyum CRM Coverage Report
[xml]
output = coverage.xml
EOF

echo "✅ .coveragerc created"

# 3. Test dependencies are managed in pyproject.toml [dependency-groups].dev.
echo "✅ Test dependencies are managed through uv and pyproject.toml."

# 4. Create test directories
mkdir -p tests/{unit/{services,repositories},integration/endpoints,factories,mocks}
mkdir -p .github/workflows
mkdir -p docs

echo "✅ Test directories created"

# 5. Test factories (tests/factories/patient.py)
cat > tests/factories/patient.py << 'EOF'
"""Patient factory for test data generation
Best practice 2026: Factory pattern with Faker
"""
import factory
from factory import fuzzy
from datetime import date, timedelta
from src.pharmaviyum.models.patients import (
    Patient,
    PatientAllergy,
    PatientCondition,
    PatientInsurance,
)

class PatientFactory(factory.async_sqlalchemy.AsyncSQLAlchemyFactory):
    """Factory for creating test patients"""
    class Meta:
        model = Patient
        exclude = ["first_name_gen", "last_name_gen"]
        # Generate names
        first_name_gen = factory.Faker("first_name")
        last_name_gen = factory.Faker("last_name")

    # Basic fields
    first_name = factory.LazyAttribute(lambda o: o.first_name_gen)
    last_name = factory.LazyAttribute(lambda o: o.last_name_gen)
    full_name = factory.LazyAttribute(lambda o: f"{o.first_name} {o.last_name}")
    phone = factory.LazyAttribute(
        lambda: f"+84{factory.Faker('numerify', text='#########').evaluate(None, None, {'locale': None})}"
    )
    email = factory.LazyAttribute(
        lambda o: f"{o.first_name.lower()}.{o.last_name.lower()}@example.com"
    )
    # Demographics
    date_of_birth = factory.LazyFunction(
        lambda: date.today() - timedelta(days=factory.Faker("random_int", min=18*365, max=80*365).evaluate(None, None, {'locale': None}))
    )
    gender = fuzzy.FuzzyChoice(["male", "female", "other"])
    # Address
    address = factory.Faker("address")
    city = factory.Faker("city")
    country = fuzzy.FuzzyChoice(["VN", "TH", "MY", "ID", "PH", "SG"])
    postal_code = factory.Faker("postcode")
    # Medical
    blood_type = fuzzy.FuzzyChoice(["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
    allergies_notes = factory.Faker("sentence")
    chronic_conditions = factory.Faker("sentence")
    # Preferences
    preferred_language = fuzzy.FuzzyChoice(["vi", "en", "zh", "ko", "ms", "id", "th"])
    preferred_notification_channel = fuzzy.FuzzyChoice(["zalo", "line", "whatsapp", "messenger"])
    # Loyalty
    loyalty_tier = fuzzy.FuzzyChoice(["Bronze", "Silver", "Gold", "Platinum"])
    loyalty_points = factory.LazyFunction(lambda: factory.Faker("random_int", min=0, max=10000).evaluate(None, None, {'locale': None}))
    visit_count = factory.LazyFunction(lambda: factory.Faker("random_int", min=0, max=100).evaluate(None, None, {'locale': None}))
    last_visit_date = factory.LazyFunction(
        lambda: date.today() - timedelta(days=factory.Faker("random_int", min=0, max=365).evaluate(None, None, {'locale': None}))
    )
    # Misc
    is_active = True
    notes = factory.Faker("paragraph")

class PatientAllergyFactory(factory.async_sqlalchemy.AsyncSQLAlchemyFactory):
    """Factory for patient allergies"""
    class Meta:
        model = PatientAllergy
        patient = factory.SubFactory(PatientFactory)
    allergen_type = fuzzy.FuzzyChoice(["drug", "food", "environmental", "other"])
    allergen_name = fuzzy.FuzzyChoice([
        "Penicillin", "Aspirin", "Ibuprofen", "Sulfa drugs",
        "Peanuts", "Shellfish", "Eggs", "Milk",
        "Pollen", "Dust mites", "Mold", "Pet dander",
    ])
    severity = fuzzy.FuzzyChoice(["mild", "moderate", "severe", "life-threatening"])
    reaction = factory.Faker("sentence")
    is_verified = fuzzy.FuzzyChoice([True, False])

class PatientConditionFactory(factory.async_sqlalchemy.AsyncSQLAlchemyFactory):
    """Factory for patient conditions"""
    class Meta:
        model = PatientCondition
        patient = factory.SubFactory(PatientFactory)
    condition_name = fuzzy.FuzzyChoice([
        "Hypertension", "Diabetes Type 2", "Asthma", "Arthritis",
        "Depression", "Anxiety", "Migraine", "Epilepsy",
    ])
    icd10_code = fuzzy.FuzzyChoice(["I10", "E11", "J45", "M15", "F32", "F41", "G43", "G40"])
    severity = fuzzy.FuzzyChoice(["mild", "moderate", "severe"])
    is_chronic = True
    status = fuzzy.FuzzyChoice(["active", "chronic", "resolved"])

class PatientInsuranceFactory(factory.async_sqlalchemy.AsyncSQLAlchemyFactory):
    """Factory for patient insurance"""
    class Meta:
        model = PatientInsurance
        patient = factory.SubFactory(PatientFactory)
    provider_name = fuzzy.FuzzyChoice([
        "Bao Viet Insurance", "PVI Insurance", "Bao Minh Insurance",
        "Manulife", "Prudential", "AIA",
    ])
    policy_number = factory.LazyAttribute(lambda o: f"POL{factory.Faker('numerify', text='########').evaluate(None, None, {'locale': None})}")
    coverage_start = factory.LazyFunction(lambda: date.today() - timedelta(days=factory.Faker("random_int", min=0, max=365).evaluate(None, None, {'locale': None})))
    coverage_end = factory.LazyFunction(lambda: date.today() + timedelta(days=factory.Faker("random_int", min=30, max=365).evaluate(None, None, {'locale': None})))
    is_primary = True
    is_active = True
EOF

echo "✅ Patient factory created"

# 6. Global fixtures (tests/conftest.py)
cat > tests/conftest.py << 'EOF'
"""Global pytest fixtures
Best practice 2026: Comprehensive test setup with database isolation
"""
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from redis import asyncio as aioredis
from httpx import AsyncClient, ASGITransport
from src.pharmaviyum.core.database import Base
from src.pharmaviyum.main import app
from src.pharmaviyum.core.config import settings

# ---------------------------------------------------------------------------
# Event loop fixture (session scoped)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
async def test_engine():
    test_db_url = settings.DATABASE_URL.replace("pharmaviyum", "pharmaviyum_test")
    engine = create_async_engine(test_db_url, echo=False, pool_pre_ping=True)
    yield engine
    await engine.dispose()

@pytest.fixture(scope="function")
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session
        await session.rollback()
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def db_session(test_db: AsyncSession) -> AsyncSession:
    return test_db

# ---------------------------------------------------------------------------
# Redis fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
async def test_redis():
    test_redis_url = settings.REDIS_URL.rstrip("/").rsplit("/", 1)[0] + "/15"
    redis = aioredis.from_url(test_redis_url, encoding="utf-8", decode_responses=True)
    await redis.flushdb()
    yield redis
    await redis.flushdb()
    await redis.close()

@pytest.fixture
def redis_client(test_redis) -> aioredis.Redis:
    return test_redis

# ---------------------------------------------------------------------------
# HTTP client fixture
# ---------------------------------------------------------------------------
@pytest.fixture
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield test_db
    app.dependency_overrides[__import__("src.pharmaviyum.core.database", fromlist=["get_db"]).get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

# ---------------------------------------------------------------------------
# Authenticated client fixture
# ---------------------------------------------------------------------------
@pytest.fixture
async def authenticated_client(client: AsyncClient, test_db: AsyncSession) -> AsyncClient:
    from src.pharmaviyum.core.security import create_access_token
    token = create_access_token(data={"sub": "1", "email": "test@example.com", "role": "admin", "is_active": True})
    client.headers["Authorization"] = f"Bearer {token}"
    return client

# ---------------------------------------------------------------------------
# Factory fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def patient_factory(test_db: AsyncSession):
    from tests.factories import PatientFactory
    PatientFactory._meta.sqlalchemy_session = test_db
    return PatientFactory

@pytest.fixture
def patient_allergy_factory(test_db: AsyncSession):
    from tests.factories import PatientAllergyFactory
    PatientAllergyFactory._meta.sqlalchemy_session = test_db
    return PatientAllergyFactory

@pytest.fixture
def patient_condition_factory(test_db: AsyncSession):
    from tests.factories import PatientConditionFactory
    PatientConditionFactory._meta.sqlalchemy_session = test_db
    return PatientConditionFactory

# ---------------------------------------------------------------------------
# Mock fixtures (using pytest-mock)
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_cache_service(mocker):
    mock = mocker.AsyncMock()
    mock.get = mocker.AsyncMock(return_value=None)
    mock.set = mocker.AsyncMock(return_value=True)
    mock.delete = mocker.AsyncMock(return_value=True)
    mocker.patch("src.pharmaviyum.services.patient.cache_service", mock)
    return mock

@pytest.fixture
def mock_event_bus(mocker):
    mock = mocker.AsyncMock()
    mock.emit = mocker.AsyncMock()
    mocker.patch("src.pharmaviyum.services.patient.event_bus", mock)
    return mock

# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_patient_data():
    return {
        "first_name": "Ibrahim",
        "last_name": "Ibrahim",
        "phone": "+84123456789",
        "email": "ibragim@example.com",
        "country": "VN",
    }

@pytest.fixture
def sample_patient_update_data():
    return {"first_name": "Ibrahim", "loyalty_tier": "Gold"}
EOF

echo "✅ Global fixtures created"

# 7. Example unit test (tests/unit/services/test_patient_service.py)
cat > tests/unit/services/test_patient_service.py << 'EOF'
"""Unit tests for PatientService
Best practice 2026: Service layer testing with mocks
"""
import pytest
from unittest.mock import AsyncMock
from src.pharmaviyum.services.patient import PatientService
from src.pharmaviyum.schemas.patient import PatientCreate, PatientUpdate
from src.pharmaviyum.models.patients import Patient

pytestmark = pytest.mark.unit

@pytest.fixture
def mock_repository():
    repo = AsyncMock()
    repo.get_by_phone = AsyncMock(return_value=None)
    repo.get_by_email = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_id_with_relations = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock(return_value=True)
    repo.soft_delete = AsyncMock(return_value=True)
    repo.search = AsyncMock(return_value=([], 0))
    repo.count = AsyncMock(return_value=0)
    repo.get_loyalty_tiers_stats = AsyncMock(return_value={})
    repo.get_country_stats = AsyncMock(return_value={})
    repo.record_visit = AsyncMock()
    return repo

@pytest.fixture
def patient_service(mock_repository, mock_cache_service, mock_event_bus):
    return PatientService(mock_repository)

@pytest.fixture
def sample_patient():
    return Patient(
        id=1,
        first_name="Ibrahim",
        last_name="Ibrahim",
        full_name="Ibrahim Ibrahim",
        phone="+84123456789",
        email="ibragim@example.com",
        country="VN",
        loyalty_tier="Bronze",
        loyalty_points=0,
        visit_count=0,
        is_active=True,
    )

class TestPatientServiceCreate:
    @pytest.mark.asyncio
    async def test_create_patient_success(self, patient_service, mock_repository, mock_event_bus):
        patient_data = PatientCreate(
            first_name="Ibrahim",
            last_name="Ibrahim",
            phone="+84123456789",
            email="ibragim@example.com",
            country="VN",
        )
        expected = Patient(id=1, first_name="Ibrahim", last_name="Ibrahim", full_name="Ibrahim Ibrahim", phone="+84123456789")
        mock_repository.create.return_value = expected
        result = await patient_service.create_patient(patient_data)
        assert result.id == 1
        assert result.full_name == "Ibrahim Ibrahim"
        mock_repository.create.assert_called_once()
        mock_event_bus.emit.assert_called_once()

# Additional tests (get, update, delete) would follow similar patterns.
EOF

echo "✅ Unit test created"

# 8. Example integration test (tests/integration/endpoints/test_patients.py)
cat > tests/integration/endpoints/test_patients.py << 'EOF'
"""Integration tests for patient endpoints
Best practice 2026: Real DB + Redis with async HTTP client
"""
import pytest

@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_patients(authenticated_client, patient_factory):
    # Create sample patients
    await patient_factory.create(first_name="Ibrahim", last_name="Ibrahim")
    await patient_factory.create(first_name="Другой", last_name="Пациент")
    # Perform search
    response = await authenticated_client.get("/api/v1/patients/?search=Ibrahim")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["items"]) == 1
    assert data["data"]["items"][0]["first_name"] == "Ibrahim"
EOF

echo "✅ Integration test created"

# 9. CI workflow (GitHub Actions)
cat > .github/workflows/ci.yml << 'EOF'
name: CI
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14.7'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip uv
          uv sync --frozen
      - name: Lint with Ruff
        run: ruff check .
  test-unit:
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: pharmaviyum_test
          POSTGRES_USER: user
          POSTGRES_PASSWORD: password
        ports: [5432:5432]
        options: >-
          --health-cmd "pg_isready -U user -d pharmaviyum_test"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports: [6379:6379]
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14.7'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip uv
          uv sync --frozen
      - name: Run unit tests with coverage
        run: |
          pytest -m unit --cov=src/pharmaviyum --cov-report=term-missing
  test-integration:
    runs-on: ubuntu-latest
    needs: test-unit
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: pharmaviyum_test
          POSTGRES_USER: user
          POSTGRES_PASSWORD: password
        ports: [5432:5432]
        options: >-
          --health-cmd "pg_isready -U user -d pharmaviyum_test"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports: [6379:6379]
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14.7'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip uv
          uv sync --frozen
      - name: Run integration tests
        run: |
          pytest -m integration
EOF

echo "✅ CI workflow created"

# 10. Documentation (docs/testing.md)
mkdir -p docs
cat > docs/testing.md << 'EOF'
# Testing Guidelines for Pharmaviyum CRM

## Project Structure
```
tests/
├── conftest.py              # Global fixtures
├── unit/                    # Unit tests (fast, mocked)
│   ├── services/
│   │   └── test_patient_service.py
│   └── repositories/
│       └── test_patient_repository.py
├── integration/             # Integration tests (real DB)
│   └── endpoints/
│       └── test_patients.py
├── factories/               # Test data factories
│   └── patient.py
└── mocks/                   # Mock services
    └── mock_pos_client.py
```

## How to Run Tests
```bash
# Install project and test dependencies
uv sync --frozen

# Run all tests with coverage
pytest --cov=src/pharmaviyum --cov-report=term-missing

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration
```

## Coverage Goals
- Minimum line coverage: **80%**
- Target for critical paths: **90%+**
- Exclusions: migrations, `__init__.py`, `main.py`

## CI/CD Integration
The GitHub Actions workflow defined in `.github/workflows/ci.yml` will automatically:
1. Lint the code with **ruff**.
2. Execute unit tests with coverage enforcement.
3. Run integration tests against temporary PostgreSQL and Redis containers.

## Best Practices
- Use **factory-boy** factories for consistent test data.
- Mock external services (cache, event bus) with **pytest-mock**.
- Follow the **Arrange‑Act‑Assert** pattern in each test.
- Keep test names descriptive, e.g. `test_create_patient_success`.
- Mark tests with appropriate markers (`@pytest.mark.unit`, `@pytest.mark.integration`).

## Troubleshooting
- **Database errors**: Ensure Docker Compose services are running (`docker-compose up -d postgres redis`).
- **Redis errors**: Verify Redis is accessible on port `6379`.
- **Import errors**: Re‑install dependencies (`uv sync --frozen`).
EOF

echo "✅ Documentation created"

echo "=========================================================================="
echo "✅ TESTING INFRASTRUCTURE SETUP COMPLETE!"
echo "=========================================================================="
