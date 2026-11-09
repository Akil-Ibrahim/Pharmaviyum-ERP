"""MCP client discovery must never trust caller-supplied roles."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.pharmaviyum.ai.mcp import client as client_module
from src.pharmaviyum.ai.mcp.client import MCPClient

def test_tool_discovery_denies_without_authenticated_context(monkeypatch):
    monkeypatch.setattr(client_module, "get_authorization_context", lambda: None)
    list_tools = MagicMock(return_value=[])
    monkeypatch.setattr(client_module.registry, "list_tools_for_role", list_tools)

    assert MCPClient().list_tools(user_role="admin") == []
    assert MCPClient().to_openai_tools(user_role="admin") == []
    list_tools.assert_not_called()

def test_tool_discovery_rejects_role_escalation(monkeypatch):
    context = SimpleNamespace(user_id=7, pharmacy_id=2, user_role="patient")
    monkeypatch.setattr(client_module, "get_authorization_context", lambda: context)
    list_tools = MagicMock(return_value=[])
    to_openai_tools = MagicMock(return_value=[])
    monkeypatch.setattr(client_module.registry, "list_tools_for_role", list_tools)
    monkeypatch.setattr(client_module.registry, "to_openai_tools", to_openai_tools)

    client = MCPClient()
    assert client.list_tools(user_role="admin") == []
    assert client.to_openai_tools(user_role="admin") == []
    assert client.get_tool_metadata("admin_only_tool") is None
    list_tools.assert_not_called()
    to_openai_tools.assert_not_called()

def test_tool_discovery_uses_authenticated_role(monkeypatch):
    context = SimpleNamespace(user_id=7, pharmacy_id=2, user_role="pharmacist")
    monkeypatch.setattr(client_module, "get_authorization_context", lambda: context)
    list_tools = MagicMock(return_value=[])
    monkeypatch.setattr(client_module.registry, "list_tools_for_role", list_tools)

    assert MCPClient().list_tools() == []
    list_tools.assert_called_once_with("pharmacist")

@pytest.mark.asyncio
async def test_registry_rejects_caller_supplied_identity_mismatch():
    from src.pharmaviyum.ai.mcp.context import (
        MCPAuthorizationContext,
        reset_mcp_context,
        set_mcp_context,
    )
    from src.pharmaviyum.ai.mcp.registry import MCPToolRegistry

    registry = MCPToolRegistry()
    token = set_mcp_context(
        MCPAuthorizationContext(user_id=7, pharmacy_id=2, user_role="patient")
    )
    try:
        with pytest.raises(PermissionError, match="context mismatch"):
            await registry.call_tool(
                "unknown_tool",
                {},
                user_role="admin",
                user_id=7,
                pharmacy_id=2,
            )
    finally:
        reset_mcp_context(token)

@pytest.mark.asyncio
async def test_write_tool_timeout_is_not_automatically_retried(monkeypatch):
    context = SimpleNamespace(user_id=7, pharmacy_id=2, user_role="pharmacist")
    monkeypatch.setattr(client_module, "get_authorization_context", lambda: context)
    metadata = SimpleNamespace(name="write_operation", execution_class="write")
    monkeypatch.setattr(
        client_module.registry,
        "get_tool",
        lambda name: (metadata, MagicMock()),
    )
    call_tool = AsyncMock(side_effect=asyncio.TimeoutError())
    monkeypatch.setattr(client_module.registry, "call_tool", call_tool)

    result = await MCPClient(max_retries=3, timeout_seconds=1).call_tool(
        "write_operation",
        {},
    )

    assert result.success is False
    assert result.error == "Tool execution timed out"
    assert call_tool.await_count == 1

@pytest.mark.asyncio
async def test_tool_exception_details_are_not_returned_to_callers(monkeypatch):
    context = SimpleNamespace(user_id=7, pharmacy_id=2, user_role="pharmacist")
    monkeypatch.setattr(client_module, "get_authorization_context", lambda: context)
    metadata = SimpleNamespace(name="patient_lookup", execution_class="read")
    monkeypatch.setattr(
        client_module.registry,
        "get_tool",
        lambda name: (metadata, MagicMock()),
    )
    call_tool = AsyncMock(
        side_effect=RuntimeError("patient_name=Alice diagnosis=private")
    )
    monkeypatch.setattr(client_module.registry, "call_tool", call_tool)

    result = await MCPClient(max_retries=0, timeout_seconds=1).call_tool(
        "patient_lookup",
        {},
    )

    assert result.success is False
    assert result.error == "Tool execution failed"
    assert "Alice" not in str(result)
    assert "diagnosis=private" not in str(result)
