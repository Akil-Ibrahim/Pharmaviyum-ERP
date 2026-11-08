"""MCP client discovery must never trust caller-supplied roles."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

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


def test_write_tool_timeout_is_not_automatically_retried(monkeypatch):
    context = SimpleNamespace(user_id=7, pharmacy_id=2, user_role="pharmacist")
    monkeypatch.setattr(client_module, "get_authorization_context", lambda: context)
    metadata = SimpleNamespace(execution_class="write")
    monkeypatch.setattr(
        client_module.registry,
        "get_tool",
        lambda name: (metadata, MagicMock()),
    )
    call_tool = AsyncMock(side_effect=asyncio.TimeoutError())
    monkeypatch.setattr(client_module.registry, "call_tool", call_tool)

    result = asyncio.run(
        MCPClient(max_retries=3, timeout_seconds=1).call_tool(
            "write_operation",
            {},
        )
    )

    assert result.success is False
    assert call_tool.await_count == 1
