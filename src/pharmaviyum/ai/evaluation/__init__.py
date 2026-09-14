"""
Evaluation Module.

Public API:
- AgentEvaluator: LLM-as-a-judge multi-dimensional evaluator
- BenchmarkRunner: Automated dataset runner with aggregation
- GOLDEN_DATASET: Pre-defined pharmaceutical test cases
"""
from .evaluator import AgentEvaluator, EvaluationResult
from .benchmark import BenchmarkRunner, BenchmarkResult
from .datasets import GOLDEN_DATASET, EvaluationCase

__all__ = [
    "AgentEvaluator",
    "EvaluationResult",
    "BenchmarkRunner",
    "BenchmarkResult",
    "GOLDEN_DATASET",
    "EvaluationCase",
]
