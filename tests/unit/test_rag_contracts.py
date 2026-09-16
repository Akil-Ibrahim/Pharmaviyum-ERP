from uuid import uuid4

from src.pharmaviyum.ai.rag.schemas import Chunk, RAGResponse, RetrievalResult
from src.pharmaviyum.ai.rag.vector_store import PgVectorStore


def test_canonical_metadata_rejects_invalid_effective_window() -> None:
    import pytest

    from src.pharmaviyum.ai.rag.schemas import CanonicalMetadata

    with pytest.raises(ValueError, match="effective_to"):
        CanonicalMetadata(
            pharmacy_id=1,
            source="guideline.pdf",
            effective_from="2026-09-10T00:00:00Z",
            effective_to="2026-09-09T00:00:00Z",
        )


def test_rag_response_materializes_stable_citations() -> None:
    chunk_id = uuid4()
    document_id = uuid4()
    chunk = Chunk(
        id=chunk_id,
        document_id=document_id,
        content="Paracetamol dosage guidance.",
        chunk_index=0,
        chunk_type="dosage",
        metadata={
            "pharmacy_id": 42,
            "source": "guideline.pdf",
            "version": "2026.09",
            "access_level": "pharmacy",
        },
        token_count=6,
    )
    result = RetrievalResult(chunk=chunk, score=0.9, retrieval_method="hybrid")
    response = RAGResponse(
        answer=f"Use the supplied guidance [src-{chunk_id}].",
        sources=[result],
        confidence=0.9,
        model_used="test",
        latency_ms=1.0,
    )

    assert response.citations[0].citation_id == f"src-{chunk_id}"
    assert response.citations[0].version == "2026.09"


def test_vector_store_rejects_metadata_without_source() -> None:
    import pytest

    with pytest.raises(ValueError, match="source"):
        PgVectorStore._require_tenant_metadata({"pharmacy_id": 42})
