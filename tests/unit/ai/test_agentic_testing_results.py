from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.pharmaviyum.ai.agentic_testing.results import (
    AgenticTestRunResult,
    StepExecutionResult,
    derive_run_status,
)


def step(status: str, *, step_index: int = 0, error: str | None = None):
    return StepExecutionResult(
        step_index=step_index,
        action="goto",
        status=status,
        duration_ms=12,
        error=error or ("Navigation failed" if status == "failed" else None),
    )


def test_all_passed_steps_produce_passed_verdict():
    assert derive_run_status([step("passed"), step("passed", step_index=1)]) == "passed"


def test_any_failed_step_produces_failed_verdict():
    assert derive_run_status([step("passed"), step("failed", step_index=1)]) == "failed"


def test_skipped_step_produces_inconclusive_verdict():
    assert (
        derive_run_status([step("passed"), step("skipped", step_index=1)])
        == "inconclusive"
    )


def test_empty_execution_is_inconclusive_not_passed():
    assert derive_run_status([]) == "inconclusive"


def test_blocked_run_takes_precedence_over_partial_steps():
    assert (
        derive_run_status([step("passed")], blocked_reason="Browser unavailable")
        == "blocked"
    )


def test_failed_step_requires_an_error_description():
    with pytest.raises(ValidationError, match="failed steps must include"):
        step("failed", error=None)


def test_run_result_rejects_caller_supplied_verdict_override():
    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError, match="must match derived status"):
        AgenticTestRunResult(
            run_id="test-run-0001",
            scenario_id="dashboard.login",
            status="passed",
            started_at=now,
            finished_at=now,
            steps=[step("failed")],
        )


def test_run_result_requires_timezone_aware_timestamps():
    now = datetime.now()
    with pytest.raises(ValidationError, match="timezone-aware"):
        AgenticTestRunResult(
            run_id="test-run-0002",
            scenario_id="dashboard.login",
            status="inconclusive",
            started_at=now,
            finished_at=now,
        )


def test_run_result_rejects_more_than_eight_steps():
    now = datetime.now(timezone.utc)
    steps = [step("passed", step_index=index) for index in range(9)]
    with pytest.raises(ValidationError):
        AgenticTestRunResult(
            run_id="test-run-0003",
            scenario_id="dashboard.login",
            status="passed",
            started_at=now,
            finished_at=now,
            steps=steps,
        )
