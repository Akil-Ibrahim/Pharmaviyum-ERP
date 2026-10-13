"""Synthetic-patient end-to-end smoke test for Mortarium LangGraph RAG."""

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

PATIENT_ID = 1001
PHARMACY_ID = 7
CHUNK_ID = UUID("a0b1c2d3-e4f5-4678-9012-abcdef123456")
DOCUMENT_ID = UUID("b0b1c2d3-e4f5-4678-9012-abcdef123456")
PATIENT_RECORD = (
    "Synthetic patient Alex Morgan, patient ID 1001. "
    "Medication list for this test: metformin 500 mg, lisinopril 10 mg, "
    "ibuprofen 200 mg OTC, and omeprazole 20 mg. "
    "Dose schedule, indication, allergies, kidney function, and current symptoms "
    "are not verified. This record contains no clinical interaction assessment."
)


class _FakeEmbeddings:
    async def embed(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]


class _PatientOnlyRetriever:
    def __init__(self) -> None:
        self.filters_seen: list[dict] = []

    async def hybrid_search(
        self, *, query, query_embedding, top_k, filters
    ) -> list[RetrievalResult]:
        self.filters_seen.append(dict(filters))
        # Simulate a patient-scoped knowledge record: it must never be returned
        # for public/pharmacy scopes or for another patient/tenant.
        if (
            filters.get("pharmacy_id") != PHARMACY_ID
            or filters.get("access_level") != "patient"
            or filters.get("patient_id") != PATIENT_ID
        ):
            return []
        chunk = Chunk(
            id=CHUNK_ID,
            document_id=DOCUMENT_ID,
            content=PATIENT_RECORD,
            chunk_index=0,
            chunk_type="general",
            token_count=40,
            metadata={
                "pharmacy_id": PHARMACY_ID,
                "patient_id": PATIENT_ID,
                "access_level": "patient",
                "country": "VN",
                "language": "en",
                "source": "synthetic_patient_record_P-1001",
                "version": "test-v1",
            },
        )
        return [
            RetrievalResult(
                chunk=chunk,
                score=0.91,
                retrieval_method="hybrid",
            )
        ]


class _FakeLLM:
    model_name = "synthetic-smoke-test-model"

    async def ainvoke(self, prompt):
        prompt_text = str(prompt)
        if "Reply with only YES or NO." in prompt_text:
            return SimpleNamespace(content="YES")
        if "Generate 2 different ways" in prompt_text:
            return SimpleNamespace(
                content=(
                    "List the medications recorded for synthetic patient 1001.\\n"
                    "Summarize the active medication list for patient 1001."
                )
            )
        if "Hypothetical answer:" in prompt_text:
            # Used only to create a retrieval query, never presented as evidence.
            return SimpleNamespace(
                content="Retrieve the patient's documented medication list."
            )
        if "Every factual claim supported by evidence MUST include" in prompt_text:
            return SimpleNamespace(
                content=(
                    "The synthetic record lists metformin 500 mg, lisinopril "
                    "10 mg, ibuprofen 200 mg OTC, and omeprazole 20 mg "
                    f"[src-{CHUNK_ID}]. The fixture does not verify dose schedule, "
                    "indication, allergies, kidney function, or current symptoms "
                    f"[src-{CHUNK_ID}]. The record contains no clinical interaction "
                    "assessment, so this result cannot establish whether dispensing "
                    "ibuprofen is appropriate "
                    f"[src-{CHUNK_ID}]. This is synthetic test data, not clinical guidance."
                )
            )
        raise AssertionError(
            f"Unexpected LLM prompt in smoke test: {prompt_text[:120]}"
        )


@pytest.mark.asyncio
async def test_mortarium_rag_runs_end_to_end_for_one_synthetic_patient():
    retriever = _PatientOnlyRetriever()
    llm = _FakeLLM()
    rag = LangGraphRAG(
        vector_store=retriever,
        embeddings=_FakeEmbeddings(),
        llm=llm,
        fast_llm=llm,
        checkpointer=MemorySaver(),
    )
    context = QueryContext(
        user_id="synthetic-pharmacist-1",
        pharmacy_id=PHARMACY_ID,
        patient_id=PATIENT_ID,
        country="VN",
        language="en",
    )

    result = await rag.run(
        "Review this synthetic patient's medication list before dispensing "
        "ibuprofen. Use only retrieved evidence, cite source IDs, flag supported "
        "safety concerns and missing information, and state when evidence is "
        "insufficient. Do not invent facts or make the dispensing decision.",
        context=context,
        thread_id="synthetic-patient-smoke-test",
    )

    assert "metformin 500 mg" in result.answer
    assert "lisinopril 10 mg" in result.answer
    assert "ibuprofen 200 mg" in result.answer
    assert "omeprazole 20 mg" in result.answer
    assert "atorvastatin 20 mg" not in result.answer
    assert f"[src-{CHUNK_ID}]" in result.answer
    assert any(source.chunk.id == CHUNK_ID for source in result.sources)
    assert any(
        citation.citation_id == f"src-{CHUNK_ID}" for citation in result.citations
    )
    assert retriever.filters_seen
    assert all(
        filters.get("pharmacy_id") == PHARMACY_ID for filters in retriever.filters_seen
    )
    assert any(
        filters.get("access_level") == "patient"
        and filters.get("patient_id") == PATIENT_ID
        for filters in retriever.filters_seen
    )
    assert result.model_used == llm.model_name
    assert "verify" in result.answer.lower()
    assert "synthetic" in result.answer.lower()
