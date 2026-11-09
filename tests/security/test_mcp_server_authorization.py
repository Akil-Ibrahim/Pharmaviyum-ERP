"""Regression tests for authenticated MCP protocol capabilities."""

import json

import pytest

from src.pharmaviyum.ai.mcp.context import (
    MCPAuthorizationContext,
    reset_mcp_context,
    set_mcp_context,
)
from src.pharmaviyum.ai.mcp.server import MCPServer


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,params",
    [
        ("tools/list", {}),
        ("tools/call", {"name": "get_patient_history", "arguments": {}}),
        ("resources/list", {}),
        ("resources/read", {"uri": "pharma://regulations/VN"}),
        ("prompts/list", {}),
        ("prompts/get", {"name": "drug_interaction_check", "arguments": {}}),
    ],
)
async def test_data_capabilities_require_authenticated_context(method, params):
    response = await MCPServer().handle_request(
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    )

    payload = json.loads(response)
    assert payload["error"]["code"] == -32001
    assert payload["error"]["message"] == "Unauthorized"


@pytest.mark.asyncio
async def test_initialize_remains_available_without_authentication():
    response = await MCPServer().handle_request(
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    )

    payload = json.loads(response)
    assert "result" in payload
    assert payload["result"]["serverInfo"]["name"] == "pharmaviyum-mcp"


@pytest.mark.asyncio
async def test_tools_list_uses_authenticated_role(monkeypatch):
    from src.pharmaviyum.ai.mcp import server as server_module

    seen_roles = []

    def list_tools_for_role(role):
        seen_roles.append(role)
        return []

    monkeypatch.setattr(
        server_module.tool_registry, "list_tools_for_role", list_tools_for_role
    )
    token = set_mcp_context(
        MCPAuthorizationContext(user_id=7, pharmacy_id=42, user_role="patient")
    )
    try:
        response = await MCPServer().handle_request(
            json.dumps(
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
            )
        )
    finally:
        reset_mcp_context(token)

    assert json.loads(response)["result"]["tools"] == []
    assert seen_roles == ["patient"]


@pytest.mark.asyncio
async def test_invalid_json_rpc_shapes_are_rejected():
    server = MCPServer()

    array_response = json.loads(await server.handle_request("[]"))
    params_response = json.loads(
        await server.handle_request(
            json.dumps(
                {"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": []}
            )
        )
    )

    assert array_response["error"]["code"] == -32600
    assert params_response["error"]["code"] == -32600
