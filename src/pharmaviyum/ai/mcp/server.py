"""
MCP Server — JSON-RPC 2.0 Protocol Implementation.

Best practice 2026:
- Compliant with Anthropic Model Context Protocol specification
- Supports tools/list, tools/call, resources/list, resources/read, prompts/list, prompts/get
- Stateless JSON-RPC request/response handling
- Ready for STDIO or SSE transport layers
"""

from __future__ import annotations

import json
from typing import Any

from src.pharmaviyum.core.logging import logger

from .prompts import prompt_registry
from .registry import registry as tool_registry
from .resources import resource_registry


class MCPServer:
    """
    Core MCP Server implementing JSON-RPC 2.0.

    Can be wrapped in FastAPI (SSE/HTTP) or run as a standalone STDIO process.
    """

    def __init__(self, name: str = "pharmaviyum-mcp", version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.capabilities = {
            "tools": {},
            "resources": {},
            "prompts": {},
        }

    async def handle_request(self, request_body: str) -> str:
        """
        Process a JSON-RPC 2.0 request and return a JSON-RPC response.
        """
        try:
            request = json.loads(request_body)
        except json.JSONDecodeError:
            return self._error_response(None, -32700, "Parse error")

        if request.get("jsonrpc") != "2.0":
            return self._error_response(request.get("id"), -32600, "Invalid Request")

        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        try:
            result = await self._route_method(method, params)
            return self._success_response(request_id, result)
        except Exception as e:
            logger.error(f"MCP method {method} failed: {e}", exc_info=True)
            return self._error_response(request_id, -32603, str(e))

    async def _route_method(self, method: str, params: dict[str, Any]) -> Any:
        """Route JSON-RPC method to appropriate handler."""

        # 1. Initialization
        if method == "initialize":
            return {
                "protocolVersion": "2024-11-05",
                "capabilities": self.capabilities,
                "serverInfo": {"name": self.name, "version": self.version},
            }

        if method == "initialized":
            return {}  # No response required for notification

        # 2. Tools
        elif method == "tools/list":
            tools = []
            for meta in tool_registry.list_tools():
                tools.append(
                    {
                        "name": meta.name,
                        "description": meta.description,
                        "inputSchema": meta.input_schema.model_json_schema(),
                    }
                )
            return {"tools": tools}

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})

            # Execute via MCP Client (which handles validation, retry, circuit breaker)
            from .client import mcp_client

            result = await mcp_client.call_tool(tool_name, tool_args)

            if result.success:
                return {
                    "content": [
                        {"type": "text", "text": json.dumps(result.data, default=str)}
                    ],
                    "isError": False,
                }
            else:
                return {
                    "content": [{"type": "text", "text": f"Error: {result.error}"}],
                    "isError": True,
                }

        # 3. Resources
        elif method == "resources/list":
            resources = []
            for res in resource_registry.list_resources():
                resources.append(res.model_dump())
            return {"resources": resources}

        elif method == "resources/read":
            uri = params.get("uri")
            # Extract kwargs from URI (simplified)
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

        # 4. Prompts
        elif method == "prompts/list":
            prompts = []
            for p in prompt_registry.list_prompts():
                prompts.append(
                    {
                        "name": p.name,
                        "description": p.description,
                        "arguments": [arg.model_dump() for arg in p.arguments],
                    }
                )
            return {"prompts": prompts}

        elif method == "prompts/get":
            name = params.get("name")
            arguments = params.get("arguments", {})
            template_text = await prompt_registry.get_prompt(name, arguments)
            return {
                "description": f"Generated prompt: {name}",
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": template_text,
                        },
                    }
                ],
            }

        else:
            raise ValueError(f"Method not found: {method}")

    def _success_response(self, request_id: Any, result: Any) -> str:
        return json.dumps(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result,
            }
        )

    def _error_response(self, request_id: Any, code: int, message: str) -> str:
        return json.dumps(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": code,
                    "message": message,
                },
            }
        )


# Global server instance
mcp_server = MCPServer()
