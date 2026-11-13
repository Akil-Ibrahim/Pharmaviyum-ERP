"""
Evaluation Module.

Public API:
- AgentEvaluator: LLM-as-a-judge multi-dimensional evaluator
- BenchmarkRunner: Automated dataset runner with aggregation
- GOLDEN_DATASET: Pre-defined pharmaceutical test cases
"""

from .benchmark import BenchmarkResult, BenchmarkRunner
from .datasets import GOLDEN_DATASET, EvaluationCase
from .evaluator import AgentEvaluator, EvaluationResult

__all__ = [
    "AgentEvaluator",
    "EvaluationResult",
    "BenchmarkRunner",
    "BenchmarkResult",
    "GOLDEN_DATASET",
    "EvaluationCase",
]
