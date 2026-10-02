"""Security policy for Mortarium MCP tool execution.

The LLM is never granted a database connection, filesystem/code access, or
arbitrary SQL/shell execution. MCP exposes only explicitly registered
business tools. Write tools are opt-in and fail closed until the authenticated
application supplies pharmacist/user confirmation.
"""

from __future__ import annotations

from typing import Any, Literal

ExecutionClass = Literal["read", "write"]

_FORBIDDEN_SCHEMA_FIELDS = {
    "sql", "raw_sql", "sql_query", "query_text", "statement",
    "shell", "shell_command", "command", "script", "code", "source_code",
    "file_path", "filesystem_path",
}


def validate_tool_schema(schema: dict[str, Any]) -> None:
    """Reject schemas exposing generic code, shell, SQL, or filesystem inputs."""
    properties = schema.get("properties", {})
    if isinstance(properties, dict):
        for name, value in properties.items():
            if str(name).lower() in _FORBIDDEN_SCHEMA_FIELDS:
                raise ValueError(
                    f"MCP tool schema exposes forbidden execution input: {name}"
                )
            if isinstance(value, dict):
                validate_tool_schema(value)

    for key in ("items", "additionalProperties"):
        value = schema.get(key)
        if isinstance(value, dict):
            validate_tool_schema(value)


def validate_execution_policy(
    execution_class: ExecutionClass,
    requires_pharmacist_confirmation: bool,
) -> None:
    """Fail closed for write tools without explicit human confirmation."""
    if execution_class == "write" and not requires_pharmacist_confirmation:
        raise ValueError(
            "MCP write tools must require explicit pharmacist/user confirmation"
        )
