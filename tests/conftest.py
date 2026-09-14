"""
Global pytest fixtures for Pharmaviyum AI tests.

Provides:
- Mock LLM providers
- Mock Redis client
- Mock database sessions
- Test data factories
- FastAPI test client
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from typing import AsyncGenerator

# ============================================================================
# Mock LLM Providers
# ============================================================================

@pytest.fixture
def mock_ollama_llm():
    """Mock Ollama LLM that returns predefined responses."""
    mock = AsyncMock()
    mock.ainvoke = AsyncMock(return_value=MagicMock(
        content="This is a mock LLM response for testing."
    ))
    mock.astream = AsyncMock(return_value=iter([
        MagicMock(content="This "),
        MagicMock(content="is "),
        MagicMock(content="a "),
        MagicMock(content="streaming "),
        MagicMock(content="response."),
    ]))
    return mock


@pytest.fixture
def mock_evaluator_llm():
    """Mock LLM for evaluation (LLM-as-a-judge)."""
    mock = AsyncMock()
    mock.ainvoke = AsyncMock(return_value=MagicMock(
        content='{"accuracy": 0.9, "safety": 1.0, "completeness": 0.85, "compliance": 0.95, "feedback": "Good response"}'
    ))
    return mock


# ============================================================================
# Mock Redis Client
# ============================================================================

@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    mock = AsyncMock()
    
    # Basic operations
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.setex = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=1)
    mock.exists = AsyncMock(return_value=0)
    mock.ping = AsyncMock(return_value=True)
    mock.keys = AsyncMock(return_value=[])
    
    # List operations
    mock.lpush = AsyncMock(return_value=1)
    mock.llen = AsyncMock(return_value=0)
    mock.lrem = AsyncMock(return_value=1)
    
    # Sorted set operations
    mock.zadd = AsyncMock(return_value=1)
    mock.zrevrange = AsyncMock(return_value=[])
    
    # Scan
    mock.scan_iter = AsyncMock(return_value=iter([]))
    
    # Close
    mock.aclose = AsyncMock()
    
    return mock


# ============================================================================
# Mock Database Session
# ============================================================================

@pytest.fixture
def mock_db_session():
    """Mock SQLAlchemy async session."""
    mock = AsyncMock()
    mock.execute = AsyncMock(return_value=MagicMock(
        fetchall=MagicMock(return_value=[]),
        fetchone=MagicMock(return_value=None),
        scalar_one=MagicMock(return_value=0),
    ))
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    mock.close = AsyncMock()
    
    # Context manager support
    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock(return_value=False)
    
    return mock


@pytest.fixture
def mock_session_factory(mock_db_session):
    """Mock session factory that returns mock session."""
    factory = MagicMock()
    factory.return_value = mock_db_session
    return factory


# ============================================================================
# Mock MCP Client
# ============================================================================

@pytest.fixture
def mock_mcp_client():
    """Mock MCP client for testing tool calls."""
    mock = AsyncMock()
    
    mock.call_tool = AsyncMock(return_value=MagicMock(
        success=True,
        data={"status": "success", "interactions": []},
        error=None,
        latency_ms=50.0,
    ))
    
    return mock


# ============================================================================
# Test Data Factories
# ============================================================================

@pytest.fixture
def sample_document():
    """Create a sample Document for testing."""
    from src.pharmaviyum.ai.rag.schemas import Document
    
    return Document(
        id="test-doc-123",
        content="Paracetamol is a common analgesic and antipyretic medication.",
        source="test_source.pdf",
        doc_type="drug_info",
        metadata={"page": 1, "source_type": "pdf"},
        country="VN",
        language="en",
    )


@pytest.fixture
def sample_chunk():
    """Create a sample Chunk for testing."""
    from src.pharmaviyum.ai.rag.schemas import Chunk
    
    return Chunk(
        id="test-chunk-456",
        document_id="test-doc-123",
        chunk_index=0,
        content="Paracetamol dosage for adults is 500mg-1000mg every 4-6 hours.",
        metadata={"source": "test.pdf", "page": 1},
    )


@pytest.fixture
def sample_query_context():
    """Create a sample QueryContext for testing."""
    from src.pharmaviyum.ai.rag.schemas import QueryContext
    
    return QueryContext(
        query="What is the dosage of Paracetamol?",
        country="VN",
        language="en",
        halal_filter=False,
        top_k=5,
    )


@pytest.fixture
def sample_patient():
    """Create a sample patient record for testing."""
    return {
        "patient_id": 123,
        "name": "Nguyen Van A",
        "age": 45,
        "conditions": ["hypertension", "diabetes"],
        "allergies": ["penicillin"],
        "current_medications": ["Warfarin", "Metformin"],
    }


# ============================================================================
# FastAPI Test Client
# ============================================================================

@pytest.fixture
def test_client():
    """Create FastAPI test client with mocked dependencies."""
    from src.pharmaviyum.main import app
    
    # Override dependencies with mocks
    from src.pharmaviyum.ai.dependencies import get_redis_client, get_ai_container
    
    async def override_get_redis():
        from tests.conftest import mock_redis
        yield mock_redis
    
    app.dependency_overrides[get_redis_client] = override_get_redis
    
    with TestClient(app) as client:
        yield client
    
    # Clear overrides
    app.dependency_overrides.clear()
