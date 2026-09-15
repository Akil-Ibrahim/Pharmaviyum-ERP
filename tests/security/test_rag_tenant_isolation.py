import pytest

from src.pharmaviyum.ai.rag.graph import LangGraphRAG
from src.pharmaviyum.ai.rag.schemas import Chunk, QueryContext, RetrievalResult
from src.pharmaviyum.ai.rag.vector_store import PgVectorStore


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
    context = QueryContext(pharmacy_id=42, country="UA", language="uk")

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
