import math

import pytest

from src.pharmaviyum.ai.mortarium_rag.quality_metrics import (
    EmbeddingQualityEvaluator,
)


def test_evaluate_retrieval_computes_rank_metrics_and_latency():
    metrics = EmbeddingQualityEvaluator.evaluate_retrieval(
        query_embeddings=[[], []],
        relevant_doc_ids=[["a", "b"], ["c"]],
        retrieved_doc_ids=[["x", "a", "b"], ["c", "d"]],
        k_values=[1, 2, 3],
        latency_ms=[10.0, 20.0],
    )

    assert metrics.samples_evaluated == 2
    assert metrics.recall_at_k == {1: 0.5, 2: 0.75, 3: 1.0}
    assert metrics.precision_at_k == {1: 0.5, 2: 0.5, 3: 0.5}
    assert metrics.mrr == 0.75
    assert metrics.ndcg_at_k[1] == 0.5
    assert metrics.ndcg_at_k[2] == pytest.approx(
        (1 / math.log2(3) / (1 + 1 / math.log2(3)) + 1) / 2
    )
    assert metrics.ndcg_at_k[3] == pytest.approx(
        (1 / math.log2(3) + 0.5) / (1 + 1 / math.log2(3)) / 2 + 0.5
    )
    assert metrics.ndcg == metrics.ndcg_at_k[3]
    assert metrics.avg_latency_ms == 15.0
    assert metrics.latency_percentiles_ms == {50: 15.0, 95: 19.5, 99: 19.9}


def test_evaluate_retrieval_excludes_queries_without_relevant_labels():
    metrics = EmbeddingQualityEvaluator.evaluate_retrieval(
        query_embeddings=[[], []],
        relevant_doc_ids=[[], ["relevant"]],
        retrieved_doc_ids=[["unlabeled"], ["miss"]],
        k_values=[1],
        latency_ms=[5.0, 15.0],
    )

    assert metrics.samples_evaluated == 1
    assert metrics.recall_at_k == {1: 0.0}
    assert metrics.precision_at_k == {1: 0.0}
    assert metrics.mrr == 0.0
    assert metrics.avg_latency_ms == 10.0


def test_evaluate_retrieval_marks_quality_metrics_unavailable_without_labels():
    metrics = EmbeddingQualityEvaluator.evaluate_retrieval(
        query_embeddings=[[]],
        relevant_doc_ids=[[]],
        retrieved_doc_ids=[["unlabeled"]],
        k_values=[1],
    )

    assert metrics.samples_evaluated == 0
    assert metrics.recall_at_k == {}
    assert metrics.precision_at_k == {}
    assert metrics.ndcg_at_k == {}
    assert metrics.ndcg is None


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        (
            {
                "query_embeddings": [[]],
                "relevant_doc_ids": [["a"]],
                "retrieved_doc_ids": [],
            },
            "same number of queries",
        ),
        (
            {
                "query_embeddings": [[]],
                "relevant_doc_ids": [["a"]],
                "retrieved_doc_ids": [["a"]],
                "k_values": [0],
            },
            "positive integers",
        ),
        (
            {
                "query_embeddings": [[]],
                "relevant_doc_ids": [["a"]],
                "retrieved_doc_ids": [["a"]],
                "latency_ms": [-1.0],
            },
            "finite non-negative values",
        ),
    ],
)
def test_evaluate_retrieval_rejects_invalid_inputs(kwargs, message):
    with pytest.raises(ValueError, match=message):
        EmbeddingQualityEvaluator.evaluate_retrieval(**kwargs)
