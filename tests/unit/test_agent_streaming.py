"""Regression tests for LangGraph token streaming execution semantics."""

import pytest

from src.pharmaviyum.ai.agents.streaming import AgentStreamManager


@pytest.mark.asyncio
async def test_streaming_does_not_invoke_graph_twice():
    class _Graph:
        def __init__(self):
            self.invoke_calls = 0

        async def astream_events(self, initial_state, config, version):
            yield {
                "event": "on_chain_end",
                "name": "PharmacistAgent",
                "data": {"output": {"answer": "Validated answer"}},
            }

        async def ainvoke(self, initial_state, config, version):
            self.invoke_calls += 1
            raise AssertionError("streaming must not replay graph execution")

    graph = _Graph()
    manager = AgentStreamManager(graph)

    events = [
        event
        async for event in manager.stream_tokens(
            {"messages": []},
            config={"configurable": {"thread_id": "test-thread"}},
        )
    ]

    assert graph.invoke_calls == 0
    assert events[-1]["type"] == "complete"
    assert events[-1]["final_state"] == {"answer": "Validated answer"}
