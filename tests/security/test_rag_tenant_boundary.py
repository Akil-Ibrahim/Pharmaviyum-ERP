import pytest

from src.pharmaviyum.ai.rag.vector_store import PgVectorStore


def test_vector_store_rejects_unscoped_retrieval() -> None:
    with pytest.raises(ValueError, match="pharmacy_id tenant filter"):
        PgVectorStore._require_tenant_filter(None)


def test_vector_store_rejects_invalid_tenant_id() -> None:
    with pytest.raises(ValueError, match="positive integer pharmacy_id"):
        PgVectorStore._require_tenant_filter({"pharmacy_id": 0})


def test_vector_store_accepts_tenant_scoped_filter() -> None:
    PgVectorStore._require_tenant_filter({"pharmacy_id": 42})


def test_vector_store_rejects_unscoped_chunk_metadata() -> None:
    with pytest.raises(ValueError, match="ingestion requires"):
        PgVectorStore._require_tenant_metadata({})


def test_vector_store_accepts_tenant_scoped_chunk_metadata() -> None:
    PgVectorStore._require_tenant_metadata({"pharmacy_id": 42})
