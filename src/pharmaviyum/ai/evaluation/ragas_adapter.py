"""Ragas 0.4 collections adapter for the LangGraph RAG evaluation pipeline.

Ragas is deliberately loaded lazily: it is an evaluation-only dependency and is
never imported by the production request path.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RagasSample:
    """One offline evaluation example; never populate it with live patient data."""

    user_input: str
    response: str
    retrieved_contexts: list[str]
    reference: str | None = None


@dataclass(frozen=True)
class RagasMetricScore:
    name: str
    value: float | None
    reason: str | None = None


@dataclass(frozen=True)
class RagasEvaluationReport:
    scores: dict[str, RagasMetricScore] = field(default_factory=dict)

    @property
    def available_scores(self) -> dict[str, float]:
        return {
            name: score.value
            for name, score in self.scores.items()
            if score.value is not None
        }


class RagasEvaluationAdapter:
    """Evaluate RAG samples with Ragas 0.4.x collections metrics.

    The evaluator LLM and embeddings are injected by the offline evaluation
    command. This keeps provider credentials and model selection out of the
    production RAG graph and makes the adapter testable without API calls.
    """

    def __init__(self, *, llm: Any, embeddings: Any) -> None:
        if llm is None or embeddings is None:
            raise ValueError("Ragas requires an evaluator LLM and embeddings")
        self.llm = llm
        self.embeddings = embeddings

    async def evaluate(self, sample: RagasSample) -> RagasEvaluationReport:
        if not sample.user_input.strip():
            raise ValueError("user_input must not be blank")
        if not sample.response.strip():
            raise ValueError("response must not be blank")
        if not sample.retrieved_contexts:
            return RagasEvaluationReport(
                scores={
                    "faithfulness": RagasMetricScore(
                        "faithfulness", None, "No retrieved contexts"
                    ),
                    "answer_relevancy": RagasMetricScore(
                        "answer_relevancy", None, "No retrieved contexts"
                    ),
                    "context_precision": RagasMetricScore(
                        "context_precision", None, "No retrieved contexts"
                    ),
                    "context_recall": RagasMetricScore(
                        "context_recall", None, "No retrieved contexts"
                    ),
                }
            )

        try:
            from ragas.metrics.collections import (
                AnswerRelevancy,
                ContextPrecisionWithReference,
                ContextRecall,
                Faithfulness,
            )
        except ImportError as exc:
            raise RuntimeError(
                "Ragas evaluation is optional. Install requirements-eval.txt "
                "in the offline evaluation environment."
            ) from exc

        metric_specs: list[tuple[str, Any, dict[str, Any]]] = [
            (
                "faithfulness",
                Faithfulness(llm=self.llm),
                {
                    "user_input": sample.user_input,
                    "response": sample.response,
                    "retrieved_contexts": sample.retrieved_contexts,
                },
            ),
            (
                "answer_relevancy",
                AnswerRelevancy(llm=self.llm, embeddings=self.embeddings),
                {
                    "user_input": sample.user_input,
                    "response": sample.response,
                    "retrieved_contexts": sample.retrieved_contexts,
                },
            ),
        ]
        if sample.reference:
            metric_specs.extend(
                [
                    (
                        "context_precision",
                        ContextPrecisionWithReference(llm=self.llm),
                        {
                            "user_input": sample.user_input,
                            "reference": sample.reference,
                            "retrieved_contexts": sample.retrieved_contexts,
                        },
                    ),
                    (
                        "context_recall",
                        ContextRecall(llm=self.llm),
                        {
                            "reference": sample.reference,
                            "retrieved_contexts": sample.retrieved_contexts,
                        },
                    ),
                ]
            )

        scores: dict[str, RagasMetricScore] = {}
        for name, metric, kwargs in metric_specs:
            result = await metric.ascore(**kwargs)
            value = float(result.value)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"Ragas metric {name} returned an invalid score")
            scores[name] = RagasMetricScore(
                name=name,
                value=value,
                reason=getattr(result, "reason", None),
            )

        if not sample.reference:
            scores["context_precision"] = RagasMetricScore(
                "context_precision", None, "Reference answer not supplied"
            )
            scores["context_recall"] = RagasMetricScore(
                "context_recall", None, "Reference answer not supplied"
            )
        return RagasEvaluationReport(scores=scores)
