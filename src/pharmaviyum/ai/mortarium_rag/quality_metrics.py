"""
Embedding Quality Metrics & Drift Monitoring.

Best practice 2026:
- Retrieval accuracy benchmarking (recall@k)
- Embedding similarity distribution monitoring
- Drift detection via statistical tests
- Prometheus metrics for quality tracking
"""

from __future__ import annotations

import math
from collections.abc import Hashable, Sequence
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np

from src.pharmaviyum.core.logging import logger


@dataclass
class RetrievalMetrics:
    """Metrics for retrieval quality evaluation."""

    recall_at_k: dict[int, float] = field(default_factory=dict)
    precision_at_k: dict[int, float] = field(default_factory=dict)
    mrr: float = 0.0  # Mean Reciprocal Rank
    ndcg: float | None = None  # NDCG at the largest requested k
    avg_latency_ms: float = 0.0
    samples_evaluated: int = 0
    ndcg_at_k: dict[int, float] = field(default_factory=dict)
    latency_percentiles_ms: dict[int, float] = field(default_factory=dict)


@dataclass
class EmbeddingDriftReport:
    """Report on embedding quality drift."""

    timestamp: datetime
    language: str
    model_name: str
    mean_similarity: float
    std_similarity: float
    drift_detected: bool
    drift_score: float  # 0.0 = no drift, 1.0 = severe drift
    recommendations: list[str] = field(default_factory=list)


class EmbeddingQualityEvaluator:
    """
    Evaluates embedding quality using standard IR metrics.

    Metrics:
    - Recall@k: % of relevant docs retrieved in top-k
    - Precision@k: % of top-k that are relevant
    - MRR: Mean Reciprocal Rank of first relevant result
    - NDCG: Quality of ranking (position-weighted)
    """

    @staticmethod
    def compute_cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        a_arr = np.array(a, dtype=np.float32)
        b_arr = np.array(b, dtype=np.float32)

        norm_a = np.linalg.norm(a_arr)
        norm_b = np.linalg.norm(b_arr)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(np.dot(a_arr, b_arr) / (norm_a * norm_b))

    @staticmethod
    def evaluate_retrieval(
        query_embeddings: Sequence[Sequence[float]],
        relevant_doc_ids: Sequence[Sequence[Hashable]],
        retrieved_doc_ids: Sequence[Sequence[Hashable]],
        k_values: Sequence[int] = (1, 5, 10),
        latency_ms: Sequence[float] | None = None,
    ) -> RetrievalMetrics:
        """
        Evaluate retrieval quality against ground truth.

        Args:
            query_embeddings: Retained for API compatibility; ranking scores are
                evaluated from document IDs and do not use embedding values.
            relevant_doc_ids: For each query, the set of relevant document IDs.
            retrieved_doc_ids: For each query, ranked document IDs.
            k_values: k values for recall/precision@k
            latency_ms: Optional measured end-to-end retrieval latency per query.

        Queries with no labeled relevant documents are excluded because recall
        and NDCG are undefined for them. Report such queries separately as
        no-answer/abstention cases.
        """
        metrics = RetrievalMetrics()
        n_queries = len(relevant_doc_ids)
        if len(query_embeddings) != n_queries or len(retrieved_doc_ids) != n_queries:
            raise ValueError(
                "query_embeddings, relevant_doc_ids, and retrieved_doc_ids "
                "must have the same number of queries"
            )
        if latency_ms is not None and len(latency_ms) != n_queries:
            raise ValueError("latency_ms must contain one value per query")
        if latency_ms is not None and any(
            not math.isfinite(value) or value < 0 for value in latency_ms
        ):
            raise ValueError("latency_ms must contain finite non-negative values")

        ks = tuple(k_values)
        if any(not isinstance(k, int) or isinstance(k, bool) or k <= 0 for k in ks):
            raise ValueError("k_values must contain positive integers")
        if len(set(ks)) != len(ks):
            raise ValueError("k_values must not contain duplicates")

        if not n_queries:
            return metrics

        recalls: dict[int, list[float]] = {k: [] for k in ks}
        precisions: dict[int, list[float]] = {k: [] for k in ks}
        ndcgs: dict[int, list[float]] = {k: [] for k in ks}
        reciprocal_ranks: list[float] = []

        for i in range(n_queries):
            relevant = set(relevant_doc_ids[i])
            if not relevant:
                continue

            retrieved = list(retrieved_doc_ids[i])
            first_relevant_rank = next(
                (
                    rank
                    for rank, doc_id in enumerate(retrieved, 1)
                    if doc_id in relevant
                ),
                None,
            )
            reciprocal_ranks.append(
                1.0 / first_relevant_rank if first_relevant_rank is not None else 0.0
            )

            for k in ks:
                top_k = retrieved[:k]
                hits = len(set(top_k) & relevant)
                recalls[k].append(hits / len(relevant))
                precisions[k].append(hits / k)

                dcg = sum(
                    1.0 / math.log2(rank + 1)
                    for rank, doc_id in enumerate(top_k, 1)
                    if doc_id in relevant
                )
                ideal_hits = min(len(relevant), k)
                idcg = sum(
                    1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1)
                )
                ndcgs[k].append(dcg / idcg if idcg else 0.0)

        if reciprocal_ranks:
            metrics.recall_at_k = {
                k: float(np.mean(values)) for k, values in recalls.items()
            }
            metrics.precision_at_k = {
                k: float(np.mean(values)) for k, values in precisions.items()
            }
            metrics.ndcg_at_k = {
                k: float(np.mean(values)) for k, values in ndcgs.items()
            }
        metrics.mrr = float(np.mean(reciprocal_ranks)) if reciprocal_ranks else 0.0
        metrics.ndcg = metrics.ndcg_at_k[max(ks)] if ks and metrics.ndcg_at_k else None
        metrics.samples_evaluated = len(reciprocal_ranks)

        if latency_ms is not None:
            if latency_ms:
                metrics.avg_latency_ms = float(np.mean(latency_ms))
                metrics.latency_percentiles_ms = {
                    percentile: float(np.percentile(latency_ms, percentile))
                    for percentile in (50, 95, 99)
                }

        return metrics

    @staticmethod
    def compute_embedding_statistics(
        embeddings: list[list[float]],
    ) -> dict[str, float]:
        """Compute basic statistics of embedding distribution."""
        if not embeddings:
            return {}

        arr = np.array(embeddings, dtype=np.float32)

        # Pairwise cosine similarities (sampled for efficiency)
        sample_size = min(1000, len(arr))
        indices = np.random.choice(len(arr), sample_size, replace=False)
        sample = arr[indices]

        # Compute pairwise similarities
        norms = np.linalg.norm(sample, axis=1, keepdims=True)
        normalized = sample / np.maximum(norms, 1e-8)
        similarities = normalized @ normalized.T

        # Extract upper triangle (excluding diagonal)
        upper_tri = similarities[np.triu_indices(len(sample), k=1)]

        return {
            "mean_similarity": float(np.mean(upper_tri)),
            "std_similarity": float(np.std(upper_tri)),
            "median_similarity": float(np.median(upper_tri)),
            "min_similarity": float(np.min(upper_tri)),
            "max_similarity": float(np.max(upper_tri)),
            "embedding_dim": arr.shape[1],
            "sample_size": sample_size,
        }


class DriftDetector:
    """
    Detects drift in embedding quality over time.

    Methods:
    - Statistical: Compare current distribution vs baseline
    - Threshold: Alert if metrics drop below threshold
    - Trend: Detect gradual degradation
    """

    def __init__(
        self,
        baseline_stats: dict[str, float] | None = None,
        drift_threshold: float = 0.1,  # 10% change triggers alert
    ):
        self.baseline = baseline_stats or {}
        self.drift_threshold = drift_threshold
        self._history: list[EmbeddingDriftReport] = []

    def detect_drift(
        self,
        current_stats: dict[str, float],
        language: str,
        model_name: str,
    ) -> EmbeddingDriftReport:
        """
        Detect drift by comparing current stats to baseline.

        Uses simple statistical distance (relative change in mean/similarity).
        """
        if not self.baseline:
            # First run — set baseline
            self.baseline = current_stats
            return EmbeddingDriftReport(
                timestamp=datetime.utcnow(),
                language=language,
                model_name=model_name,
                mean_similarity=current_stats.get("mean_similarity", 0.0),
                std_similarity=current_stats.get("std_similarity", 0.0),
                drift_detected=False,
                drift_score=0.0,
                recommendations=["Baseline established"],
            )

        # Compute drift score (relative change in mean similarity)
        baseline_mean = self.baseline.get("mean_similarity", 0.0)
        current_mean = current_stats.get("mean_similarity", 0.0)

        if baseline_mean > 0:
            relative_change = abs(current_mean - baseline_mean) / baseline_mean
        else:
            relative_change = 0.0

        drift_detected = relative_change > self.drift_threshold
        recommendations = []

        if drift_detected:
            recommendations.append(
                f"Significant drift detected ({relative_change:.1%}). "
                "Consider re-embedding documents or updating model."
            )

            if current_mean < baseline_mean:
                recommendations.append(
                    "Similarity decreased — check for data quality issues "
                    "or model degradation."
                )

        report = EmbeddingDriftReport(
            timestamp=datetime.utcnow(),
            language=language,
            model_name=model_name,
            mean_similarity=current_mean,
            std_similarity=current_stats.get("std_similarity", 0.0),
            drift_detected=drift_detected,
            drift_score=relative_change,
            recommendations=recommendations,
        )

        self._history.append(report)

        if drift_detected:
            logger.warning(
                f"Embedding drift detected for {language}/{model_name}",
                extra={
                    "drift_score": relative_change,
                    "baseline_mean": baseline_mean,
                    "current_mean": current_mean,
                },
            )

        return report

    def get_history(self, limit: int = 10) -> list[EmbeddingDriftReport]:
        """Get recent drift reports."""
        return self._history[-limit:]

    def update_baseline(self, new_stats: dict[str, float]):
        """Manually update baseline (e.g., after re-embedding)."""
        self.baseline = new_stats
        logger.info("Drift detection baseline updated")
