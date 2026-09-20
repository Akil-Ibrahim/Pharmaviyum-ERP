"""
Benchmark Runner for Agent Evaluation.

Best practice 2026:
- Automated execution of Golden Dataset against AgentHarness
- Aggregation of metrics (pass rate, latency, safety violations)
- LangSmith dataset logging for historical tracking
- Async concurrent execution for speed
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from src.pharmaviyum.ai.observability.tracer import tracer
from src.pharmaviyum.core.logging import logger

from .datasets import GOLDEN_DATASET, EvaluationCase
from .evaluator import AgentEvaluator, EvaluationResult


@dataclass
class BenchmarkResult:
    """Aggregated results of a benchmark run."""

    total_cases: int
    passed_cases: int
    failed_cases: int
    avg_latency_ms: float
    safety_violations: int
    tool_call_accuracy: float  # % of cases where expected tools were called
    detailed_results: list[dict[str, Any]] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        return (
            (self.passed_cases / self.total_cases) * 100
            if self.total_cases > 0
            else 0.0
        )


class BenchmarkRunner:
    """
    Runs the Golden Dataset against the AgentHarness and evaluates results.
    """

    def __init__(
        self,
        agent_harness,
        evaluator: AgentEvaluator,
        dataset: list[EvaluationCase] = GOLDEN_DATASET,
    ):
        self.harness = agent_harness
        self.evaluator = evaluator
        self.dataset = dataset

    async def run(self, concurrency: int = 3) -> BenchmarkResult:
        """
        Execute benchmark with controlled concurrency.
        """
        logger.info(
            f"Starting benchmark run on {len(self.dataset)} cases (concurrency={concurrency})"
        )
        start_time = time.perf_counter()

        semaphore = asyncio.Semaphore(concurrency)
        tasks = [self._evaluate_case(case, semaphore) for case in self.dataset]
        detailed_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate metrics
        passed = 0
        failed = 0
        safety_violations = 0
        total_latency = 0.0
        tool_call_hits = 0

        processed_results: list[dict[str, Any]] = []
        for i, result in enumerate(detailed_results):
            case = self.dataset[i]

            if isinstance(result, Exception):
                logger.error(
                    f"Benchmark case {case.id} failed with exception: {result}"
                )
                failed += 1
                processed_results.append(
                    {"case_id": case.id, "status": "error", "error": str(result)}
                )
                continue

            eval_result: EvaluationResult = result["eval_result"]
            agent_answer = result["agent_answer"]
            latency = result["latency_ms"]
            tools_called = result["tools_called"]

            total_latency += latency

            if eval_result.passed:
                passed += 1
            else:
                failed += 1

            if eval_result.safety < 0.9 or case.expected_safety_level == "blocked":
                safety_violations += 1

            # Check tool call accuracy
            expected_tools = set(case.expected_tools_called)
            actual_tools = set(tools_called)
            if expected_tools.issubset(actual_tools) or not expected_tools:
                tool_call_hits += 1

            processed_results.append(
                {
                    "case_id": case.id,
                    "category": case.category,
                    "passed": eval_result.passed,
                    "scores": {
                        "accuracy": eval_result.accuracy,
                        "safety": eval_result.safety,
                        "completeness": eval_result.completeness,
                        "compliance": eval_result.compliance,
                    },
                    "latency_ms": latency,
                    "tools_called": tools_called,
                    "feedback": eval_result.feedback,
                }
            )

            # Log to LangSmith
            tracer.log_evaluation(
                query=case.query,
                answer=agent_answer,
                evaluation_result=eval_result.model_dump(),
                session_id=f"benchmark_{case.id}",
            )

        total_cases = len(self.dataset)
        avg_latency = total_latency / total_cases if total_cases > 0 else 0.0
        tool_accuracy = (tool_call_hits / total_cases) * 100 if total_cases > 0 else 0.0

        final_result = BenchmarkResult(
            total_cases=total_cases,
            passed_cases=passed,
            failed_cases=failed,
            avg_latency_ms=round(avg_latency, 2),
            safety_violations=safety_violations,
            tool_call_accuracy=round(tool_accuracy, 2),
            detailed_results=processed_results,
        )

        total_time = time.perf_counter() - start_time

        logger.info(
            "Benchmark run completed",
            extra={
                "pass_rate": f"{final_result.pass_rate:.1f}%",
                "avg_latency_ms": final_result.avg_latency_ms,
                "safety_violations": final_result.safety_violations,
                "tool_accuracy": f"{final_result.tool_call_accuracy:.1f}%",
                "total_time_seconds": round(total_time, 2),
            },
        )

        return final_result

    async def _evaluate_case(
        self, case: EvaluationCase, semaphore: asyncio.Semaphore
    ) -> dict[str, Any]:
        """Evaluate a single case."""
        async with semaphore:
            start = time.perf_counter()

            # Run agent
            agent_result = await self.harness.run(
                session_id=f"bench_{case.id}",
                query=case.query,
                context=case.context,
            )

            latency_ms = (time.perf_counter() - start) * 1000
            agent_answer = agent_result.get("answer", "")
            tools_called = [r.get("tool") for r in agent_result.get("tool_results", [])]

            # Evaluate response
            eval_result = await self.evaluator.evaluate(
                query=case.query,
                answer=agent_answer,
                context=case.context,
            )

            return {
                "eval_result": eval_result,
                "agent_answer": agent_answer,
                "latency_ms": latency_ms,
                "tools_called": tools_called,
            }
