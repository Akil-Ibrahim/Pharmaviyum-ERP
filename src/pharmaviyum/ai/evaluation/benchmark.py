"""
Benchmark Runner for Agent Evaluation.

Runs the golden dataset and aggregates quality, latency, safety, and tool-use
metrics. Metrics are computed from observed outcomes; expected blocking alone
is not considered a safety violation.
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
    tool_call_accuracy: float  # % of cases with an exact tool-set match
    detailed_results: list[dict[str, Any]] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        return (
            (self.passed_cases / self.total_cases) * 100
            if self.total_cases > 0
            else 0.0
        )


class BenchmarkRunner:
    """Runs the Golden Dataset against the AgentHarness and evaluates results."""

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
        """Execute the benchmark with controlled concurrency."""
        if concurrency < 1:
            raise ValueError("concurrency must be at least 1")

        logger.info(
            f"Starting benchmark run on {len(self.dataset)} cases (concurrency={concurrency})"
        )
        start_time = time.perf_counter()

        semaphore = asyncio.Semaphore(concurrency)
        tasks = [self._evaluate_case(case, semaphore) for case in self.dataset]
        detailed_results = await asyncio.gather(*tasks, return_exceptions=True)

        passed = 0
        failed = 0
        safety_violations = 0
        total_latency = 0.0
        latency_cases = 0
        tool_call_hits = 0
        processed_results: list[dict[str, Any]] = []

        for i, result in enumerate(detailed_results):
            case = self.dataset[i]

            if isinstance(result, BaseException):
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
            latency_cases += 1

            if eval_result.passed:
                passed += 1
            else:
                failed += 1

            safety_violation = eval_result.safety < 0.9
            if safety_violation:
                safety_violations += 1

            expected_tools = set(case.expected_tools_called)
            actual_tools = set(tools_called)
            tools_match = expected_tools == actual_tools
            if tools_match:
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
                    "expected_tools": sorted(expected_tools),
                    "unexpected_tools": sorted(actual_tools - expected_tools),
                    "tool_calls_match": tools_match,
                    "safety_violation": safety_violation,
                    "feedback": eval_result.feedback,
                }
            )

            tracer.log_evaluation(
                query=case.query,
                answer=agent_answer,
                evaluation_result=eval_result.model_dump(),
                session_id=f"benchmark_{case.id}",
            )

        total_cases = len(self.dataset)
        avg_latency = total_latency / latency_cases if latency_cases else 0.0
        tool_accuracy = (tool_call_hits / total_cases) * 100 if total_cases else 0.0

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
        """Run the agent and evaluate its answer against available sources."""
        async with semaphore:
            start = time.perf_counter()
            agent_result = await self.harness.run(
                session_id=f"bench_{case.id}",
                query=case.query,
                context=case.context,
            )
            latency_ms = (time.perf_counter() - start) * 1000
            agent_answer = agent_result.get("answer", "")
            tools_called = [
                item.get("tool")
                for item in agent_result.get("tool_results", [])
                if item.get("tool")
            ]
            sources = agent_result.get("sources")
            if sources is None:
                sources = agent_result.get("retrieved_sources", [])

            eval_result = await self.evaluator.evaluate(
                query=case.query,
                answer=agent_answer,
                sources=sources,
                context=case.context,
            )
            return {
                "eval_result": eval_result,
                "agent_answer": agent_answer,
                "latency_ms": latency_ms,
                "tools_called": tools_called,
            }
