import pytest

from src.pharmaviyum.ai.mortarium_rag.vector_store import PgVectorStore


def test_vector_store_rejects_unscoped_retrieval() -> None:
    with pytest.raises(ValueError, match="pharmacy_id tenant filter"):
        PgVectorStore._require_tenant_filter(None)


def test_vector_store_rejects_invalid_tenant_id() -> None:
    with pytest.raises(ValueError, match="positive integer pharmacy_id"):
        PgVectorStore._require_tenant_filter({"pharmacy_id": 0})


def test_vector_store_accepts_tenant_scoped_filter() -> None:
    PgVectorStore._require_tenant_filter({"pharmacy_id": 42})


def test_vector_store_rejects_non_canonical_chunk_metadata() -> None:
    with pytest.raises(ValueError, match="source"):
        PgVectorStore._require_tenant_metadata({"pharmacy_id": 42})


def test_vector_store_accepts_canonical_chunk_metadata() -> None:
    PgVectorStore._require_tenant_metadata(
        {
            "pharmacy_id": 42,
            "source": "guideline.pdf",
            "country": "VN",
            "language": "vi",
            "access_level": "pharmacy",
        }
    )
