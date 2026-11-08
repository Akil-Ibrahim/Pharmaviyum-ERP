"""Agent execution budget and tool-state regression tests."""

from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage

from src.pharmaviyum.ai.agents.pharmacist_agent import PharmacistAgent


class _MCPClient:
    def __init__(self):
        self.calls = []

    async def call_tool(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(success=True, data={"ok": True}, error=None)


def _tool_calls(count: int) -> list[dict]:
    return [
        {
            "name": "check_drug_interactions",
            "args": {"patient_id": index + 1},
            "id": f"tool-{index}",
        }
        for index in range(count)
    ]


@pytest.mark.asyncio
async def test_executor_enforces_cumulative_tool_call_budget():
    agent = PharmacistAgent.__new__(PharmacistAgent)
    agent.mcp_client = _MCPClient()
    state = {
        "messages": [AIMessage(content="", tool_calls=_tool_calls(12))],
        "context": {
            "user_id": 7,
            "pharmacy_id": 42,
            "user_role": "pharmacist",
            "trace_id": "trace",
        },
        "tool_results": [],
    }

    result = await agent.executor_node(state)

    assert len(agent.mcp_client.calls) == 10
    assert len(result["messages"]) == 12
    assert len(result["tool_results"]) == 12
    assert all("input_data" not in item for item in result["tool_results"])
    assert [
        item["error"]
        for item in result["tool_results"][-2:]
    ] == ["tool_call_budget_exceeded", "tool_call_budget_exceeded"]


@pytest.mark.asyncio
async def test_executor_rejects_new_calls_after_budget_is_exhausted():
    agent = PharmacistAgent.__new__(PharmacistAgent)
    agent.mcp_client = _MCPClient()
    state = {
        "messages": [AIMessage(content="", tool_calls=_tool_calls(2))],
        "context": {
            "user_id": 7,
            "pharmacy_id": 42,
            "user_role": "pharmacist",
            "trace_id": "trace",
        },
        "tool_results": [{"tool": "previous", "success": True}] * 10,
    }

    result = await agent.executor_node(state)

    assert agent.mcp_client.calls == []
    assert len(result["messages"]) == 2
    assert all(
        item["error"] == "tool_call_budget_exceeded"
        for item in result["tool_results"]
    )
