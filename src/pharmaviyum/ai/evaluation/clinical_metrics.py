"""Deterministic and judge-assisted pharmaceutical RAG evaluation metrics.

These metrics complement Ragas. They are offline evaluation utilities, not
runtime clinical guardrails or a substitute for pharmacist/clinical review.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Awaitable, Callable, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class MetricResult:
    name: str
    score: float | None
    passed: bool | None
    details: Mapping[str, object]


@dataclass(frozen=True)
class MedicationEntity:
    name: str
    strength: str
    dosage_form: str

    def normalized(self) -> tuple[str, str, str]:
        return tuple(
            re.sub(r"\s+", " ", value).strip().casefold()
            for value in (self.name, self.strength, self.dosage_form)
        )  # type: ignore[return-value]


@dataclass(frozen=True)
class NegationExpectation:
    """A labeled proposition and the polarity expressed in the generated answer."""

    proposition_id: str
    expected_negative: bool
    answer_negative: bool


ClaimSupportJudge = Callable[[str, str], Awaitable[bool]]


def _f1(expected: set[tuple[str, ...]], predicted: set[tuple[str, ...]]) -> float:
    if not expected and not predicted:
        return 1.0
    if not expected or not predicted:
        return 0.0
    true_positive = len(expected & predicted)
    precision = true_positive / len(predicted)
    recall = true_positive / len(expected)
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


async def citation_correctness(
    *,
    answer: str,
    sources: Mapping[str, str],
    supports_claim: ClaimSupportJudge | None,
) -> MetricResult:
    """Check that each factual sentence cites a real source that entails it.

    A syntactically valid citation is not considered correct unless an
    independent entailment judge confirms that the cited source supports the
    associated claim. Without that judge the metric is explicitly unavailable.
    """
    if supports_claim is None:
        return MetricResult(
            "citation_correctness",
            None,
            None,
            {"reason": "An entailment judge is required to verify claim support"},
        )
    sentences = [
        part.strip()
        for part in re.split(r"(?<=[.!?])\s+", answer)
        if part.strip()
    ]
    factual = [part for part in sentences if re.search(r"\w", part)]
    if not factual:
        return MetricResult(
            "citation_correctness", 1.0, True, {"claims": 0, "supported": 0}
        )

    supported = 0
    invalid_citations = 0
    for claim in factual:
        citation_ids = set(re.findall(r"\[(src-[0-9a-fA-F-]{36})\]", claim))
        valid_sources = [sources[item] for item in citation_ids if item in sources]
        if not valid_sources:
            invalid_citations += 1
            continue
        if any([await supports_claim(claim, source) for source in valid_sources]):
            supported += 1
    score = supported / len(factual)
    return MetricResult(
        "citation_correctness",
        score,
        score == 1.0,
        {
            "claims": len(factual),
            "supported": supported,
            "invalid_or_missing_citations": invalid_citations,
        },
    )


def medication_entity_accuracy(
    *,
    expected: Sequence[MedicationEntity],
    predicted: Sequence[MedicationEntity],
) -> MetricResult:
    """Exact precision/recall/F1 over medication name + strength + dosage form."""
    expected_set = {item.normalized() for item in expected}
    predicted_set = {item.normalized() for item in predicted}
    score = _f1(expected_set, predicted_set)
    return MetricResult(
        "medication_entity_accuracy",
        score,
        score == 1.0,
        {
            "expected_count": len(expected_set),
            "predicted_count": len(predicted_set),
            "missing": sorted(expected_set - predicted_set),
            "unexpected": sorted(predicted_set - expected_set),
        },
    )


def negation_preservation(
    expectations: Sequence[NegationExpectation],
) -> MetricResult:
    """Measure polarity preservation against manually labeled propositions."""
    if not expectations:
        return MetricResult(
            "negation_preservation", None, None, {"reason": "No labeled propositions"}
        )
    preserved = sum(
        item.expected_negative == item.answer_negative for item in expectations
    )
    score = preserved / len(expectations)
    return MetricResult(
        "negation_preservation",
        score,
        score == 1.0,
        {"propositions": len(expectations), "preserved": preserved},
    )


async def clinical_hallucination_rate(
    *,
    clinical_claims: Sequence[str],
    evidence: Sequence[str],
    supports_claim: ClaimSupportJudge | None,
) -> MetricResult:
    """Fraction of clinical claims not supported by supplied evidence."""
    if supports_claim is None:
        return MetricResult(
            "clinical_hallucination_rate",
            None,
            None,
            {"reason": "An entailment judge is required"},
        )
    if not clinical_claims:
        return MetricResult(
            "clinical_hallucination_rate", 0.0, True, {"claims": 0, "unsupported": 0}
        )
    unsupported = 0
    for claim in clinical_claims:
        if not evidence or not any(
            [await supports_claim(claim, item) for item in evidence]
        ):
            unsupported += 1
    rate = unsupported / len(clinical_claims)
    return MetricResult(
        "clinical_hallucination_rate",
        rate,
        rate == 0.0,
        {"claims": len(clinical_claims), "unsupported": unsupported},
    )


def patient_context_isolation(
    *,
    expected_pharmacy_id: int,
    expected_patient_id: int | None,
    source_metadata: Iterable[Mapping[str, object]],
) -> MetricResult:
    """Fail closed on cross-pharmacy or cross-patient private evidence."""
    violations: list[str] = []
    checked = 0
    for metadata in source_metadata:
        access_level = str(metadata.get("access_level", "pharmacy"))
        pharmacy_id = metadata.get("pharmacy_id")
        patient_id = metadata.get("patient_id")
        if access_level == "public":
            continue
        checked += 1
        if access_level not in {"pharmacy", "patient"}:
            violations.append("invalid_access_level")
        if pharmacy_id != expected_pharmacy_id:
            violations.append("pharmacy_scope_mismatch")
        if access_level == "patient":
            if expected_patient_id is None or patient_id != expected_patient_id:
                violations.append("patient_scope_mismatch")
    passed = not violations
    return MetricResult(
        "patient_context_isolation",
        1.0 if passed else 0.0,
        passed,
        {"private_sources_checked": checked, "violations": violations},
    )


def multilingual_retrieval(
    *,
    language: str,
    expected_source_ids: Sequence[str],
    retrieved_source_ids: Sequence[str],
) -> MetricResult:
    """Recall of gold source IDs, reported separately for Russian and English."""
    normalized_language = language.casefold().split("-")[0]
    if normalized_language not in {"ru", "en"}:
        raise ValueError("Only Russian (ru) and English (en) are in this evaluation")
    expected = set(expected_source_ids)
    retrieved = set(retrieved_source_ids)
    if not expected:
        return MetricResult(
            f"multilingual_retrieval_{normalized_language}",
            None,
            None,
            {"reason": "No gold relevant source IDs"},
        )
    hits = len(expected & retrieved)
    score = hits / len(expected)
    return MetricResult(
        f"multilingual_retrieval_{normalized_language}",
        score,
        score == 1.0,
        {"language": normalized_language, "relevant": len(expected), "retrieved": hits},
    )
