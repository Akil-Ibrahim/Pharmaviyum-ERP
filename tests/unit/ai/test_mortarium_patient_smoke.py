"""End-to-end synthetic patient smoke test for the Mortarium LangGraph RAG pipeline.

All clinical content is explicitly synthetic test evidence. This test validates
pipeline wiring and tenant/patient scoping, not clinical accuracy of an LLM.
"""

from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID

import pytest
from langgraph.checkpoint.memory import MemorySaver

from src.pharmaviyum.ai.mortarium_rag.graph import LangGraphRAG
from src.pharmaviyum.ai.mortarium_rag.schemas import (
    Chunk,
    QueryContext,
    RetrievalResult,
)


PATIENT_ID = 42001
PHARMACY_ID = 7
PATIENT_CHUNK_ID = UUID("a1a1a1a1-1111-4111-8111-a1a1a1a1a1a1")
GUIDELINE_CHUNK_ID = UUID("b2b2b2b2-2222-4222-8222-b2b2b2b2b2b2")


def _hit(
    *,
    chunk_id: UUID,
    content: str,
    source: str,
    access_level: str,
    patient_id: int | None = None,
    chunk_type: str = "general",
) -> RetrievalResult:
    metadata = {
        "pharmacy_id": PHARMACY_ID,
        "country": "VN",
        "language": "en",
        "source": source,
        "version": "synthetic-test-v1",
        "access_level": access_level,
    }
    if patient_id is not None:
        metadata["patient_id"] = patient_id
    return RetrievalResult(
        chunk=Chunk(
            id=chunk_id,
            document_id=chunk_id,
            chunk_index=0,
            content=content,
            chunk_type=chunk_type,
            metadata=metadata,
            token_count=max(1, len(content) // 4),
        ),
        score=0.9,
        retrieval_method="hybrid",
    )


class _FakeEmbeddings:
    async def embed(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]


class _SyntheticPatientRetriever:
    """A deterministic retriever that enforces the requested test scope."""

    def __init__(self) -> None:
        self.filters_seen: list[dict[str, object]] = []
        self.patient_record = _hit(
            chunk_id=PATIENT_CHUNK_ID,
            source="synthetic-patient-record",
            access_level="patient",
            patient_id=PATIENT_ID,
            chunk_type="general",
            content=(
                "SYNTHETIC PATIENT John Miller (patient ID 42001). "
                "Medication list supplied for testing only: metformin 500 mg, "
                "lisinopril 10 mg, ibuprofen 200 mg OTC, and omeprazole 20 mg. "
                "Dose, schedule, indication, kidney function, allergy status, "
                "and current symptoms are not verified in this fixture."
            ),
        )
        self.guideline = _hit(
            chunk_id=GUIDELINE_CHUNK_ID,
            source="synthetic-pharmacy-review-checklist",
            access_level="pharmacy",
            chunk_type="interactions",
            content=(
                "SYNTHETIC TEST CHECKLIST, NOT A CLINICAL GUIDELINE. "
                "Before dispensing, verify the complete medication list, "
                "indication, dose, duration, allergies, relevant history, and "
                "current symptoms. Escalate a possible interaction for a "
                "pharmacist's assessment; do not infer that a combination is safe "
                "from a medication list alone."
            ),
        )

    async def hybrid_search(
        self,
        *,
        query: str,
        query_embedding: list[float],
        top_k: int,
        filters: dict[str, object],
    ) -> list[RetrievalResult]:
        self.filters_seen.append(dict(filters))
        if filters.get("pharmacy_id") != PHARMACY_ID:
            return []
        if filters.get("access_level") == "patient":
            if filters.get("patient_id") != PATIENT_ID:
                return []
            return [self.patient_record]
        if filters.get("access_level") == "pharmacy":
            return [self.guideline]
        return []


class _FakeLLM:
    model_name = "synthetic-smoke-test-llm"

    async def ainvoke(self, prompt: str) -> SimpleNamespace:
        if "Generate 2 different ways" in prompt:
            return SimpleNamespace(
                content=(
                    "review ibuprofen against John Miller's listed medicines\n"
                    "check missing patient safety information before dispensing"
                )
            )
        if "Hypothetical answer:" in prompt:
            return SimpleNamespace(
                content=(
                    "Medication review requires checking the complete list, "
                    "patient factors, and relevant interaction evidence."
                )
            )
        if "Reply with only YES or NO." in prompt:
            return SimpleNamespace(content="YES")
        if "Rate each sentence's relevance" in prompt:
            return SimpleNamespace(content="[[0, 0.9], [1, 0.8], [2, 0.7]]")
        if "Every factual claim supported by evidence MUST include" in prompt:
            return SimpleNamespace(
                content=(
                    "This synthetic record lists metformin 500 mg, lisinopril "
                    "10 mg, ibuprofen 200 mg OTC, and omeprazole 20 mg "
                    f"[src-{PATIENT_CHUNK_ID}]. The fixture does not verify dose "
                    "schedule, indication, allergies, kidney function, or current "
                    "symptoms [src-{PATIENT_CHUNK_ID}]. Verify the complete "
                    "medication list and relevant patient factors before deciding "
                    f"whether to dispense [src-{GUIDELINE_CHUNK_ID}]. This test "
                    "checklist is synthetic and is not clinical evidence."
                )
            )
        return SimpleNamespace(content="YES")


@pytest.mark.asyncio
async def test_synthetic_patient_medication_review_runs_through_langgraph() -> None:
    retriever = _SyntheticPatientRetriever()
    llm = _FakeLLM()
    rag = LangGraphRAG(
        vector_store=retriever,
        embeddings=_FakeEmbeddings(),
        llm=llm,
        fast_llm=llm,
        checkpointer=MemorySaver(),
    )
    context = QueryContext(
        user_id="synthetic-pharmacist",
        pharmacy_id=PHARMACY_ID,
        patient_id=PATIENT_ID,
        country="VN",
        language="en",
    )
    question = (
        "Review the synthetic patient's medication list before dispensing "
        "ibuprofen. What must the pharmacist verify, and what information is missing?"
    )

    response = await rag.run(question, context, thread_id="synthetic-patient-smoke")

    assert "metformin" in response.answer.lower()
    assert "verify" in response.answer.lower()
    assert response.sources
    assert {str(source.chunk.id) for source in response.sources} == {
        str(PATIENT_CHUNK_ID),
        str(GUIDELINE_CHUNK_ID),
    }
    assert {citation.chunk_id for citation in response.citations} == {
        PATIENT_CHUNK_ID,
        GUIDELINE_CHUNK_ID,
    }
    assert all(filters["pharmacy_id"] == PHARMACY_ID for filters in retriever.filters_seen)
    patient_filters = [
        filters for filters in retriever.filters_seen
        if filters.get("access_level") == "patient"
    ]
    assert patient_filters
    assert all(filters.get("patient_id") == PATIENT_ID for filters in patient_filters)
    assert "synthetic" in response.answer.lower()
