from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from src.pharmaviyum.ai.agentic_testing.results import (
    AgenticTestRunResult,
    StepExecutionResult,
    derive_run_status,
)


def step(status: str, **overrides) -> StepExecutionResult:
    values = {
        "step_index": 0,
        "action": "expect_url",
        "status": status,
        "duration_ms": 25,
    }
    if status == "failed":
        values["error"] = "Expected /sign-in but observed /"
    values.update(overrides)
    return StepExecutionResult.model_validate(values)


def test_all_passed_steps_produce_passed_verdict():
    assert derive_run_status([step("passed")]) == "passed"


def test_any_failed_step_produces_failed_verdict():
    assert derive_run_status([step("passed"), step("failed", step_index=1)]) == "failed"


def test_skipped_step_produces_inconclusive_verdict():
    assert derive_run_status([step("passed"), step("skipped", step_index=1)]) == "inconclusive"


def test_empty_execution_is_inconclusive_not_passed():
    assert derive_run_status([]) == "inconclusive"


def test_blocked_run_takes_precedence_over_partial_steps():
    assert derive_run_status([step("passed")], blocked_reason="Browser unavailable") == "blocked"


def test_failed_step_requires_an_error_description():
    with pytest.raises(ValidationError, match="failed steps must include"):
        step("failed", error=None)


def test_run_result_rejects_ai_or_caller_overridden_verdict():
    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError, match="deterministic step verdict"):
        AgenticTestRunResult(
            run_id="test-run-0001",
            scenario_id="dashboard.login",
            status="passed",
            started_at=now,
            finished_at=now + timedelta(seconds=1),
            steps=[step("failed")],
        )


def test_run_result_requires_timezone_aware_timestamps():
    now = datetime(2026, 11, 28, 12, 0, 0)
    with pytest.raises(ValidationError, match="timezone"):
        AgenticTestRunResult(
            run_id="test-run-0002",
            scenario_id="dashboard.login",
            status="passed",
            started_at=now,
            finished_at=now + timedelta(seconds=1),
            steps=[step("passed")],
        )


def test_run_result_rejects_more_than_eight_steps():
    now = datetime.now(timezone.utc)
    steps = [
        step("passed", step_index=index)
        for index in range(9)
    ]
    with pytest.raises(ValidationError):
        AgenticTestRunResult(
            run_id="test-run-0003",
            scenario_id="dashboard.login",
            status="passed",
            started_at=now,
            finished_at=now + timedelta(seconds=1),
            steps=steps,
        )
