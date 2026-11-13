"""Regression tests preventing implicit Vietnam defaults in global AI context."""

import pytest


@pytest.mark.unit
def test_ai_query_defaults_to_neutral_jurisdiction_and_english():
    from src.pharmaviyum.api.v1.ai import QueryRequest

    request = QueryRequest(query="What is this medicine?", pharmacy_id=1)

    assert request.country is None
    assert request.language == "en"


@pytest.mark.unit
def test_rag_query_context_does_not_assume_a_country():
    from src.pharmaviyum.ai.mortarium_rag.schemas import QueryContext

    context = QueryContext(user_id="test-user", pharmacy_id=1)

    assert context.country is None
    assert context.language == "en"


@pytest.mark.unit
def test_rag_document_metadata_does_not_assume_a_country():
    from src.pharmaviyum.ai.mortarium_rag.schemas import CanonicalMetadata, Document

    metadata = CanonicalMetadata(pharmacy_id=1, source="global-reference.pdf")
    document = Document(
        content="General medicine reference information.",
        source="global-reference.pdf",
        doc_type="drug_info",
    )

    assert metadata.country is None
    assert metadata.language == "en"
    assert document.country is None
    assert document.language == "en"
