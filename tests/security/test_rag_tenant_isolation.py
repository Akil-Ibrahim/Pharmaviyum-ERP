import pytest

from src.pharmaviyum.ai.mortarium_rag.graph import LangGraphRAG
from src.pharmaviyum.ai.mortarium_rag.schemas import (
    Chunk,
    QueryContext,
    RetrievalResult,
)
from src.pharmaviyum.ai.mortarium_rag.vector_store import PgVectorStore


def test_rag_requires_positive_tenant_id():
    with pytest.raises(ValueError, match="pharmacy_id"):
        PgVectorStore._require_tenant_filter(None)

    with pytest.raises(ValueError, match="positive integer"):
        PgVectorStore._require_tenant_filter({"pharmacy_id": 0})

    with pytest.raises(ValueError, match="positive integer"):
        PgVectorStore._require_tenant_filter({"pharmacy_id": True})


def test_rag_ingestion_requires_tenant_metadata():
    with pytest.raises(ValueError, match="pharmacy_id"):
        PgVectorStore._require_tenant_metadata({})

    with pytest.raises(ValueError, match="positive integer"):
        PgVectorStore._require_tenant_metadata({"pharmacy_id": 0})


def test_rag_build_filters_always_contains_tenant():
    rag = object.__new__(LangGraphRAG)
    context = QueryContext(
        user_id="test-user", pharmacy_id=42, country="UA", language="uk"
    )

    filters = rag._build_filters(context)

    assert filters["pharmacy_id"] == 42
    assert filters["country"] == "UA"


def test_retrieval_result_preserves_tenant_metadata():
    chunk = Chunk(
        document_id="00000000-0000-0000-0000-000000000001",
        content="tenant scoped source",
        chunk_index=0,
        token_count=3,
        metadata={"pharmacy_id": 42, "source": "guideline.pdf"},
    )
    result = RetrievalResult(
        chunk=chunk,
        score=0.9,
        retrieval_method="hybrid",
    )

    assert result.chunk.metadata["pharmacy_id"] == 42
    assert result.chunk.metadata["source"] == "guideline.pdf"


def test_canonical_tenant_metadata_cannot_be_overridden_by_extra_fields():
    import json

    metadata = {
        "pharmacy_id": 42,
        "source": "guideline.pdf",
        "country": "UA",
        "language": "uk",
        "access_level": "pharmacy",
        "category": "clinical",
        "custom": "extension-field",
    }

    persisted = json.loads(PgVectorStore._serialize_metadata(metadata))

    assert persisted["pharmacy_id"] == 42
    assert persisted["source"] == "guideline.pdf"
    assert persisted["custom"] == "extension-field"


def test_rag_access_level_filter_sets_include_public_and_pharmacy():
    context = QueryContext(
        user_id="test-user", pharmacy_id=42, country="UA", language="uk"
    )
    filters = LangGraphRAG._build_filter_sets(context)

    assert {item["access_level"] for item in filters} == {"public", "pharmacy"}
    assert all(item["pharmacy_id"] == 42 for item in filters)


def test_rag_patient_filter_requires_authenticated_patient_scope():
    context = QueryContext(
        user_id="test-user",
        pharmacy_id=42,
        patient_id=7,
        country="UA",
        language="uk",
    )
    filters = LangGraphRAG._build_filter_sets(context)

    patient_filters = [item for item in filters if item["access_level"] == "patient"]
    assert patient_filters == [
        {
            "pharmacy_id": 42,
            "country": "UA",
            "access_level": "patient",
            "patient_id": 7,
        }
    ]


def test_patient_metadata_requires_patient_id():
    from src.pharmaviyum.ai.mortarium_rag.schemas import CanonicalMetadata

    with pytest.raises(ValueError, match="requires patient_id"):
        CanonicalMetadata(
            pharmacy_id=42,
            source="patient-record.pdf",
            access_level="patient",
        )
