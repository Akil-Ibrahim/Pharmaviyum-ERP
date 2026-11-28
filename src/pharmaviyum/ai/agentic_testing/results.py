"""Deterministic execution-result contracts for agentic QA runs."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field, model_validator

StepStatus = Literal["passed", "failed", "skipped"]
RunStatus = Literal["passed", "failed", "blocked", "inconclusive"]


class StepExecutionResult(BaseModel):
    """Observed outcome of one approved browser-test step."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    step_index: int = Field(ge=0)
    action: Literal["goto", "expect_url", "expect_visible"]
    status: StepStatus
    duration_ms: int = Field(ge=0)
    observed: str | None = Field(default=None, max_length=2048)
    error: str | None = Field(default=None, max_length=2048)
    evidence_refs: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def failed_step_must_explain_failure(self) -> StepExecutionResult:
        if self.status == "failed" and not self.error:
            raise ValueError("failed steps must include an error description")
        return self


class AgenticTestRunResult(BaseModel):
    """Machine-readable run result; status is derived from observed step outcomes."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str = Field(min_length=8, max_length=100)
    scenario_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{2,99}$")
    status: RunStatus
    started_at: datetime
    finished_at: datetime
    steps: list[StepExecutionResult] = Field(max_length=8)
    blocked_reason: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_timestamps_and_verdict(self) -> AgenticTestRunResult:
        if self.started_at.tzinfo is None or self.finished_at.tzinfo is None:
            raise ValueError("run timestamps must include timezone information")
        if self.finished_at < self.started_at:
            raise ValueError("finished_at must not precede started_at")
        expected_status = derive_run_status(
            self.steps, blocked_reason=self.blocked_reason
        )
        if self.status != expected_status:
            raise ValueError(
                f"run status must match deterministic step verdict: {expected_status}"
            )
        return self


def derive_run_status(
    steps: Sequence[StepExecutionResult],
    *,
    blocked_reason: str | None = None,
) -> RunStatus:
    """Derive a conservative verdict; missing or skipped evidence never passes."""
    if blocked_reason:
        return "blocked"
    if not steps:
        return "inconclusive"
    if any(step.status == "failed" for step in steps):
        return "failed"
    if any(step.status == "skipped" for step in steps):
        return "inconclusive"
    return "passed"
