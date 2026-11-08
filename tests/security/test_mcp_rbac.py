import pytest
from pydantic import BaseModel

from src.pharmaviyum.ai.mcp.client import MCPClient
from src.pharmaviyum.ai.mcp.registry import MCPToolRegistry


class _Input(BaseModel):
    value: str


class _Output(BaseModel):
    value: str


@pytest.mark.asyncio
async def test_registry_filters_tools_by_role() -> None:
    registry = MCPToolRegistry()

    @registry.tool(
        name="pharmacist_only",
        description="Restricted tool",
        input_schema=_Input,
        output_schema=_Output,
        required_roles=["pharmacist"],
    )
    async def pharmacist_only(data: _Input) -> _Output:
        return _Output(value=data.value)

    @registry.tool(
        name="patient_tool",
        description="Patient tool",
        input_schema=_Input,
        output_schema=_Output,
        required_roles=["patient"],
    )
    async def patient_tool(data: _Input) -> _Output:
        return _Output(value=data.value)

    assert [tool.name for tool in registry.list_tools_for_role("patient")] == [
        "patient_tool"
    ]
    assert [tool.name for tool in registry.list_tools_for_role("pharmacist")] == [
        "pharmacist_only"
    ]


@pytest.mark.asyncio
async def test_mcp_client_fails_closed_without_authorization_context() -> None:
    client = MCPClient(max_retries=0)

    result = await client.call_tool(
        tool_name="does_not_matter",
        input_data={},
    )

    assert result.success is False
    assert result.error == "MCP authorization and tenant context are required"


@pytest.mark.asyncio
async def test_mcp_client_rejects_unauthorized_role(monkeypatch) -> None:
    from src.pharmaviyum.ai.mcp import client as client_module

    registry = client_module.registry
    original = dict(registry._tools)

    @registry.tool(
        name="restricted_test_tool",
        description="Restricted test tool",
        input_schema=_Input,
        output_schema=_Output,
        required_roles=["pharmacist"],
    )
    async def restricted_test_tool(data: _Input) -> _Output:
        return _Output(value=data.value)

    async def healthy(_: str) -> dict[str, str]:
        return {"status": "healthy", "details": ""}

    from src.pharmaviyum.ai.mcp import tool_management

    monkeypatch.setattr(tool_management.health_checker, "check_tool_health", healthy)

    from src.pharmaviyum.ai.mcp.context import (
        MCPAuthorizationContext,
        reset_mcp_context,
        set_mcp_context,
    )

    token = set_mcp_context(
        MCPAuthorizationContext(user_id=1, pharmacy_id=1, user_role="patient")
    )
    try:
        result = await MCPClient(max_retries=0).call_tool(
            tool_name="restricted_test_tool",
            input_data={"value": "secret"},
            user_role="patient",
            user_id=1,
            pharmacy_id=1,
        )
        assert result.success is False
        assert result.error is not None
        assert "not authorized" in result.error
    finally:
        reset_mcp_context(token)
        registry._tools.clear()
        registry._tools.update(original)
