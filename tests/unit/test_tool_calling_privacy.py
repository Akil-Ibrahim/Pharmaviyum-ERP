"""Privacy and cancellation contracts for parallel MCP tool execution."""

import asyncio
from unittest.mock import MagicMock

import pytest

from src.pharmaviyum.ai.harness.tool_calling import ToolCallingLayer, ToolSpec


@pytest.mark.asyncio
async def test_parallel_tool_exception_is_redacted_from_tool_record():
    layer = ToolCallingLayer(
        mcp_client=MagicMock(),
        tool_specs={"patient_lookup": ToolSpec(name="patient_lookup")},
    )

    async def fail_with_sensitive_error(tool_call, trace_id=None):
        raise RuntimeError("patient_name=Alice diagnosis=private")

    layer._execute_single_tool = fail_with_sensitive_error

    results = await layer.execute_tools(
        [
            {
                "name": "patient_lookup",
                "args": {"patient_id": 123},
                "id": "call-1",
            }
        ]
    )

    assert len(results) == 1
    assert results[0].success is False
    assert results[0].error == "Tool execution failed"
    assert "Alice" not in results[0].error


@pytest.mark.asyncio
async def test_parallel_tool_cancellation_is_propagated():
    layer = ToolCallingLayer(
        mcp_client=MagicMock(),
        tool_specs={"patient_lookup": ToolSpec(name="patient_lookup")},
    )

    async def cancel(tool_call, trace_id=None):
        raise asyncio.CancelledError()

    layer._execute_single_tool = cancel

    with pytest.raises(asyncio.CancelledError):
        await layer.execute_tools(
            [{"name": "patient_lookup", "args": {}, "id": "call-1"}]
        )
