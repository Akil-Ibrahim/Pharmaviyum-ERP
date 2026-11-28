"""Deterministic LangGraph planner for bounded browser-test scenarios.

This graph validates and plans work only. A separate Playwright runner remains the
sole authority for browser observations and pass/fail outcomes.
"""

from __future__ import annotations

from typing import Literal, TypedDict
from uuid import uuid4

from langgraph.graph import END, StateGraph

from .schemas import AgenticTestScenario, validate_scenario_target


class AgenticTestingState(TypedDict, total=False):
    scenario: dict
    allowed_origins: list[str]
    run_id: str
    status: Literal["planned", "rejected"]
    target_origin: str
    execution_plan: list[dict]
    error: str


def _validate_node(state: AgenticTestingState) -> dict:
    try:
        scenario = AgenticTestScenario.model_validate(state.get("scenario", {}))
        target_origin = validate_scenario_target(
            scenario, state.get("allowed_origins", [])
        )
        return {
            "scenario": scenario.model_dump(mode="json"),
            "target_origin": target_origin,
            "run_id": state.get("run_id") or str(uuid4()),
            "status": "planned",
            "error": "",
        }
    except (TypeError, ValueError) as exc:
        return {
            "run_id": state.get("run_id") or str(uuid4()),
            "status": "rejected",
            "execution_plan": [],
            "error": str(exc)[:500],
        }


def _plan_node(state: AgenticTestingState) -> dict:
    if state.get("status") != "planned":
        return {"execution_plan": []}
    scenario = AgenticTestScenario.model_validate(state["scenario"])
    return {
        "execution_plan": [
            {
                "step_index": index,
                "action": step.action,
                "value": step.value,
                "target_origin": state["target_origin"],
            }
            for index, step in enumerate(scenario.steps)
        ]
    }


def build_agentic_testing_graph():
    """Compile a small, side-effect-free validation/planning state machine."""
    workflow = StateGraph(AgenticTestingState)
    workflow.add_node("validate_scenario", _validate_node)
    workflow.add_node("build_execution_plan", _plan_node)
    workflow.set_entry_point("validate_scenario")
    workflow.add_edge("validate_scenario", "build_execution_plan")
    workflow.add_edge("build_execution_plan", END)
    return workflow.compile()
