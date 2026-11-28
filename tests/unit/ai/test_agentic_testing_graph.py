from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.pharmaviyum.ai.agentic_testing.graph import build_agentic_testing_graph
from src.pharmaviyum.ai.agentic_testing.schemas import (
    AgenticTestScenario,
    BrowserTestStep,
    normalized_origin,
)


@pytest.fixture
def graph():
    return build_agentic_testing_graph()


def scenario(target_url: str = "http://127.0.0.1:4173/") -> dict:
    return {
        "scenario_id": "dashboard.unauthenticated_redirect",
        "title": "Unauthenticated users are redirected to sign in",
        "target_url": target_url,
        "steps": [
            {"action": "goto", "value": "/"},
            {"action": "expect_url", "value": "/sign-in"},
            {"action": "expect_visible", "value": "Sign in to Pharmaviyum"},
        ],
        "expected_outcome": "The browser is redirected to the sign-in page.",
    }


def test_graph_builds_bounded_plan_for_explicit_test_origin(graph):
    result = graph.invoke(
        {
            "scenario": scenario(),
            "allowed_origins": ["http://127.0.0.1:4173"],
            "run_id": "test-run-001",
        }
    )

    assert result["status"] == "planned"
    assert result["run_id"] == "test-run-001"
    assert result["target_origin"] == "http://127.0.0.1:4173"
    assert [step["action"] for step in result["execution_plan"]] == [
        "goto",
        "expect_url",
        "expect_visible",
    ]
    assert all(
        step["target_origin"] == "http://127.0.0.1:4173"
        for step in result["execution_plan"]
    )


def test_graph_rejects_unlisted_or_public_target(graph):
    result = graph.invoke(
        {
            "scenario": scenario("https://pharmaviyum-erp.fastapicloud.dev/"),
            "allowed_origins": ["http://127.0.0.1:4173"],
        }
    )

    assert result["status"] == "rejected"
    assert result["execution_plan"] == []
    assert "allowlist" in result["error"]


def test_graph_fails_closed_when_origin_allowlist_is_missing(graph):
    result = graph.invoke({"scenario": scenario(), "allowed_origins": []})

    assert result["status"] == "rejected"
    assert result["execution_plan"] == []
    assert "explicitly configured" in result["error"]


def test_scenario_rejects_arbitrary_or_cross_origin_navigation():
    invalid = scenario()
    invalid["steps"][0]["value"] = "https://example.com/"
    with pytest.raises(ValidationError):
        AgenticTestScenario.model_validate(invalid)


def test_scenario_rejects_more_than_eight_steps():
    invalid = scenario()
    invalid["steps"] = [{"action": "expect_url", "value": "/"}] * 9
    with pytest.raises(ValidationError):
        AgenticTestScenario.model_validate(invalid)


def test_browser_step_rejects_unknown_action_and_extra_fields():
    with pytest.raises(ValidationError):
        BrowserTestStep.model_validate({"action": "execute_shell", "value": "ls"})
    with pytest.raises(ValidationError):
        BrowserTestStep.model_validate(
            {"action": "expect_url", "value": "/", "script": "alert(1)"}
        )


def test_origin_normalization_rejects_credentials_and_paths():
    with pytest.raises(ValueError, match="credentials"):
        normalized_origin("https://user:secret@example.com")
    with pytest.raises(ValueError, match="path"):
        normalized_origin("https://example.com/app")
