from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.pharmaviyum.ai.evaluation.clinical_metrics import (
    MedicationEntity,
    NegationExpectation,
    citation_correctness,
    clinical_hallucination_rate,
    medication_entity_accuracy,
    multilingual_retrieval,
    negation_preservation,
    patient_context_isolation,
)
from src.pharmaviyum.ai.evaluation.ragas_adapter import (
    RagasEvaluationAdapter,
    RagasSample,
)


@pytest.mark.unit
def test_medication_entity_accuracy_checks_name_strength_and_form():
    expected = [MedicationEntity("Amoxicillin", "500 mg", "capsule")]
    correct = medication_entity_accuracy(expected=expected, predicted=expected)
    wrong_strength = medication_entity_accuracy(
        expected=expected,
        predicted=[MedicationEntity("Amoxicillin", "250 mg", "capsule")],
    )
    assert correct.score == 1.0
    assert wrong_strength.score == 0.0
    assert wrong_strength.passed is False


@pytest.mark.unit
def test_negation_preservation_detects_lost_negation():
    result = negation_preservation(
        [
            NegationExpectation("allergy", True, True),
            NegationExpectation("pregnancy", True, False),
        ]
    )
    assert result.score == 0.5
    assert result.passed is False


@pytest.mark.unit
def test_patient_context_isolation_rejects_other_patient():
    result = patient_context_isolation(
        expected_pharmacy_id=10,
        expected_patient_id=42,
        source_metadata=[
            {"access_level": "patient", "pharmacy_id": 10, "patient_id": 99}
        ],
    )
    assert result.score == 0.0
    assert "patient_scope_mismatch" in result.details["violations"]


@pytest.mark.unit
@pytest.mark.parametrize(("language", "expected"), [("ru", 0.5), ("en", 1.0)])
def test_multilingual_retrieval_reports_language_specific_recall(language, expected):
    result = multilingual_retrieval(
        language=language,
        expected_source_ids=["a", "b"],
        retrieved_source_ids=["a"],
    )
    assert result.score == expected


@pytest.mark.unit
@pytest.mark.asyncio
async def test_citation_correctness_requires_real_source_and_entailment():
    judge = AsyncMock(side_effect=lambda claim, source: source in claim)
    result = await citation_correctness(
        answer=(
            "Amoxicillin treats infection "
            "[src-00000000-0000-0000-0000-000000000001]."
        ),
        sources={
            "src-00000000-0000-0000-0000-000000000001": (
                "Amoxicillin treats infection"
            )
        },
        supports_claim=judge,
    )
    assert result.score == 1.0
    assert result.passed is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_clinical_hallucination_rate_counts_unsupported_claims():
    judge = AsyncMock(side_effect=lambda claim, evidence: claim in evidence)
    result = await clinical_hallucination_rate(
        clinical_claims=["Supported fact", "Unsupported dose"],
        evidence=["Supported fact"],
        supports_claim=judge,
    )
    assert result.score == 0.5
    assert result.passed is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ragas_adapter_validates_empty_context_without_model_calls():
    adapter = RagasEvaluationAdapter(llm=object(), embeddings=object())
    report = await adapter.evaluate(
        RagasSample(
            user_input="What is this medicine?",
            response="Insufficient evidence.",
            retrieved_contexts=[],
        )
    )
    assert report.scores["faithfulness"].value is None
    assert report.scores["faithfulness"].reason == "No retrieved contexts"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ragas_adapter_rejects_blank_input():
    adapter = RagasEvaluationAdapter(llm=object(), embeddings=object())
    with pytest.raises(ValueError, match="user_input"):
        await adapter.evaluate(
            RagasSample(user_input=" ", response="answer", retrieved_contexts=["doc"])
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ragas_adapter_scores_standard_metrics_with_reference(monkeypatch):
    class FakeMetric:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        async def ascore(self, **kwargs):
            return SimpleNamespace(value=0.9, reason="supported")

    collections = ModuleType("ragas.metrics.collections")
    for metric_name in (
        "AnswerRelevancy",
        "ContextPrecisionWithReference",
        "ContextRecall",
        "Faithfulness",
    ):
        setattr(collections, metric_name, FakeMetric)
    ragas_module = ModuleType("ragas")
    metrics_module = ModuleType("ragas.metrics")
    monkeypatch.setitem(__import__("sys").modules, "ragas", ragas_module)
    monkeypatch.setitem(__import__("sys").modules, "ragas.metrics", metrics_module)
    monkeypatch.setitem(
        __import__("sys").modules, "ragas.metrics.collections", collections
    )

    adapter = RagasEvaluationAdapter(llm=object(), embeddings=object())
    report = await adapter.evaluate(
        RagasSample(
            user_input="What is the medicine?",
            response="It is a tablet.",
            retrieved_contexts=["The medicine is a tablet."],
            reference="The medicine is a tablet.",
        )
    )

    assert set(report.available_scores) == {
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        "context_recall",
    }
    assert all(score == 0.9 for score in report.available_scores.values())
