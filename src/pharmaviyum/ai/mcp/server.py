"""
MCP Server — authenticated JSON-RPC 2.0 protocol implementation.

Initialization is public protocol negotiation. Every data-bearing method
requires an authenticated, tenant-scoped MCPAuthorizationContext.
"""

from __future__ import annotations

import json
from typing import Any

from src.pharmaviyum.core.logging import logger

from .context import require_mcp_context
from .prompts import prompt_registry
from .registry import registry as tool_registry
from .resources import resource_registry


class MCPServer:
    """Core MCP server; the hosting transport must establish trusted context."""

    def __init__(self, name: str = "pharmaviyum-mcp", version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.capabilities: dict[str, dict[str, Any]] = {
            "tools": {},
            "resources": {},
            "prompts": {},
        }

    async def handle_request(self, request_body: str) -> str:
        """Validate JSON-RPC input and return non-sensitive protocol errors."""
        try:
            request = json.loads(request_body)
        except (json.JSONDecodeError, TypeError):
            return self._error_response(None, -32700, "Parse error")

        if not isinstance(request, dict) or request.get("jsonrpc") != "2.0":
            request_id = request.get("id") if isinstance(request, dict) else None
            return self._error_response(request_id, -32600, "Invalid Request")

        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        if not isinstance(method, str) or not isinstance(params, dict):
            return self._error_response(request_id, -32600, "Invalid Request")

        try:
            result = await self._route_method(method, params)
            return self._success_response(request_id, result)
        except PermissionError:
            logger.warning("MCP request denied", extra={"method": method})
            return self._error_response(request_id, -32001, "Unauthorized")
        except LookupError:
            return self._error_response(request_id, -32601, "Method not found")
        except ValueError:
            logger.warning("MCP request has invalid parameters", extra={"method": method})
            return self._error_response(request_id, -32602, "Invalid params")
        except Exception as exc:
            # Exception strings and tracebacks may contain clinical data.
            logger.error(
                "MCP request failed",
                extra={"method": method, "error_type": type(exc).__name__},
            )
            return self._error_response(request_id, -32603, "Internal error")

    async def _route_method(self, method: str, params: dict[str, Any]) -> Any:
        """Route methods after authenticating all non-initialization requests."""
        if method == "initialize":
            return {
                "protocolVersion": "2024-11-05",
                "capabilities": self.capabilities,
                "serverInfo": {"name": self.name, "version": self.version},
            }

        if method == "initialized":
            return {}

        # All resource, prompt and tool operations require trusted identity.
        context = require_mcp_context()

        if method == "tools/list":
            tools = [
                {
                    "name": meta.name,
                    "description": meta.description,
                    "inputSchema": meta.input_schema.model_json_schema(),
                }
                for meta in tool_registry.list_tools_for_role(context.user_role)
            ]
            return {"tools": tools}

        if method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            if not isinstance(tool_name, str) or not isinstance(tool_args, dict):
                raise ValueError("Invalid tool call parameters")

            from .client import mcp_client

            result = await mcp_client.call_tool(tool_name, tool_args)
            if result.success:
                return {
                    "content": [
                        {"type": "text", "text": json.dumps(result.data, default=str)}
                    ],
                    "isError": False,
                }
            # Do not expose exception messages, SQL fragments or PHI to the model.
            return {
                "content": [{"type": "text", "text": "Tool execution failed"}],
                "isError": True,
            }

        if method == "resources/list":
            return {
                "resources": [
                    resource.model_dump()
                    for resource in resource_registry.list_resources()
                ]
            }

        if method == "resources/read":
            uri = params.get("uri")
            if not isinstance(uri, str):
                raise ValueError("Invalid resource URI")
            content = await resource_registry.read_resource(uri)
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": content,
                    }
                ]
            }

        if method == "prompts/list":
            return {
                "prompts": [
                    {
                        "name": prompt.name,
                        "description": prompt.description,
                        "arguments": [
                            argument.model_dump() for argument in prompt.arguments
                        ],
                    }
                    for prompt in prompt_registry.list_prompts()
                ]
            }

        if method == "prompts/get":
            name = params.get("name")
            arguments = params.get("arguments", {})
            if not isinstance(name, str) or not isinstance(arguments, dict):
                raise ValueError("Invalid prompt parameters")
            template_text = await prompt_registry.get_prompt(name, arguments)
            return {
                "description": f"Generated prompt: {name}",
                "messages": [
                    {
                        "role": "user",
                        "content": {"type": "text", "text": template_text},
                    }
                ],
            }

        raise LookupError("Method not found")

    def _success_response(self, request_id: Any, result: Any) -> str:
        return json.dumps(
            {"jsonrpc": "2.0", "id": request_id, "result": result},
            default=str,
        )

    def _error_response(self, request_id: Any, code: int, message: str) -> str:
        return json.dumps(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": code, "message": message},
            }
        )


mcp_server = MCPServer()
