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
    PgVectorStore._require_tenant_filter(
        {"pharmacy_id": 7, "access_level": "pharmacy"}
    )


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



@pytest.mark.parametrize(
    "access_level,patient_id",
    [
        ("pharmacy", 42),
        ("public", 42),
    ],
)
def test_non_patient_metadata_rejects_patient_identifier(access_level, patient_id):
    with pytest.raises(ValueError, match="only valid when access_level"):
        CanonicalMetadata.model_validate(
            {
                "pharmacy_id": 7,
                "source": "pharmacy-record",
                "access_level": access_level,
                "patient_id": patient_id,
            }
        )


@pytest.mark.parametrize(
    "filters,match",
    [
        (
            {"pharmacy_id": 7},
            "explicit valid access_level",
        ),
        (
            {"pharmacy_id": 7, "access_level": "patient"},
            "exact patient_id",
        ),
        (
            {"pharmacy_id": 7, "patient_id": 42},
            "access_level='patient'",
        ),
        (
            {"pharmacy_id": 7, "access_level": "patient", "patient_id": True},
            "positive integer patient_id",
        ),
        (
            {"pharmacy_id": 7, "access_level": "patient", "patient_id": 0},
            "positive integer patient_id",
        ),
        (
            {"pharmacy_id": 7, "access_level": "patient", "patient_id": "42"},
            "positive integer patient_id",
        ),
        (
            {"pharmacy_id": 7, "access_level": "unknown"},
            "access_level is invalid",
        ),
    ],
)
def test_retrieval_rejects_ambiguous_or_invalid_patient_scope(filters, match):
    with pytest.raises(ValueError, match=match):
        PgVectorStore._require_tenant_filter(filters)


def test_retrieval_accepts_exact_patient_scope():
    PgVectorStore._require_tenant_filter(
        {"pharmacy_id": 7, "access_level": "patient", "patient_id": 42}
    )


def test_patient_filter_clause_keeps_patient_and_pharmacy_as_bound_parameters():
    store = PgVectorStore(session_factory=lambda: None)
    clause, params = store._build_filter_clause(
        {"pharmacy_id": 7, "access_level": "patient", "patient_id": 42}
    )

    assert "metadata ->> 'pharmacy_id'" in clause
    assert "metadata ->> 'access_level'" in clause
    assert "metadata ->> 'patient_id'" in clause
    assert set(params.values()) == {7, "patient", 42}


@pytest.mark.parametrize("field,value", [("pharmacy_id", True), ("patient_id", "42")])
def test_canonical_metadata_rejects_coerced_identifier_types(field, value):
    metadata = {
        "pharmacy_id": 7,
        "source": "patient-record",
        "access_level": "patient",
        "patient_id": 42,
    }
    metadata[field] = value

    with pytest.raises(ValueError):
        CanonicalMetadata.model_validate(metadata)
