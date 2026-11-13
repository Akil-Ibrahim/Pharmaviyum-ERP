"""Security regression tests for Mortarium RAG tenant and metadata contracts."""

import pytest

from src.pharmaviyum.ai.mortarium_rag.graph import LangGraphRAG
from src.pharmaviyum.ai.mortarium_rag.schemas import CanonicalMetadata, QueryContext
from src.pharmaviyum.ai.mortarium_rag.vector_store import PgVectorStore


@pytest.mark.parametrize(
    "filters",
    [
        None,
        {},
        {"country": "VN"},
        {"pharmacy_id": 0},
        {"pharmacy_id": -1},
        {"pharmacy_id": True},
        {"pharmacy_id": "7"},
    ],
)
def test_retrieval_rejects_missing_or_invalid_tenant_scope(filters):
    with pytest.raises(ValueError, match="pharmacy_id"):
        PgVectorStore._require_tenant_filter(filters)


def test_retrieval_accepts_positive_integer_tenant_scope():
    PgVectorStore._require_tenant_filter({"pharmacy_id": 7})


def test_metadata_requires_positive_pharmacy_id():
    with pytest.raises(ValueError):
        CanonicalMetadata.model_validate({"pharmacy_id": 0, "source": "approved-sop"})


def test_patient_scoped_metadata_requires_patient_id():
    with pytest.raises(ValueError, match="patient_id"):
        CanonicalMetadata.model_validate(
            {
                "pharmacy_id": 7,
                "source": "patient-record",
                "access_level": "patient",
            }
        )


def test_filter_builder_rejects_untrusted_sql_identifier():
    store = PgVectorStore(session_factory=lambda: None)
    with pytest.raises(ValueError, match="Invalid metadata filter key"):
        store._build_filter_clause({"pharmacy_id": 7, "country') OR TRUE --": "VN"})


def test_query_filter_sets_keep_patient_records_explicitly_scoped():
    context = QueryContext(
        user_id="test-user",
        pharmacy_id=7,
        patient_id=42,
        country="VN",
        language="en",
    )

    filter_sets = LangGraphRAG._build_filter_sets(context)

    assert {filters["access_level"] for filters in filter_sets} == {
        "public",
        "pharmacy",
        "patient",
    }
    patient_filters = next(
        filters for filters in filter_sets if filters["access_level"] == "patient"
    )
    assert patient_filters["pharmacy_id"] == 7
    assert patient_filters["patient_id"] == 42
