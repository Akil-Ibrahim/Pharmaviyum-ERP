"""Shared pytest fixtures for the Pharmaviyum CRM test suite."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_evaluator_llm():
    """Mock evaluator LLM with a safe default judgment."""
    mock = MagicMock()
    mock.ainvoke = AsyncMock(
        return_value=MagicMock(
            content='{"accuracy": 0.9, "safety": 0.95, "completeness": 0.85, "compliance": 0.95, "feedback": "Safe evaluation."}'
        )
    )
    return mock


@pytest.fixture
def mock_mcp_client():
    """Mock MCP client for testing tool calls."""
    mock = AsyncMock()
    mock.call_tool = AsyncMock(
        return_value=MagicMock(
            success=True,
            data={"status": "success", "interactions": []},
            error=None,
            latency_ms=50.0,
        )
    )
    return mock


@pytest.fixture
def mock_cache_service():
    """Mock the patient service cache without requiring Redis."""
    mock = MagicMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    with patch("src.pharmaviyum.services.patient.cache_service", mock):
        yield mock


@pytest.fixture
def mock_event_bus():
    """Mock patient events without requiring the event bus backend."""
    mock = MagicMock()
    mock.emit = AsyncMock()
    with patch("src.pharmaviyum.services.patient.event_bus", mock):
        yield mock


@pytest.fixture
def sample_document():
    """Create a sample Document for testing."""
    from src.pharmaviyum.ai.mortarium_rag.schemas import Document

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
    from src.pharmaviyum.ai.mortarium_rag.schemas import Chunk

    return Chunk(
        id="test-chunk-456",
        document_id="test-doc-123",
        chunk_index=0,
        content="Paracetamol dosage for adults is 500mg-1000mg every 4-6 hours.",
        metadata={"source": "test.pdf", "page": 1},
        token_count=12,
    )


@pytest.fixture
def sample_query_context():
    """Create a tenant-scoped QueryContext for testing."""
    from src.pharmaviyum.ai.mortarium_rag.schemas import QueryContext

    return QueryContext(
        pharmacy_id=1,
        country="VN",
        language="en",
        halal_filter=False,
        max_tokens=1024,
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
