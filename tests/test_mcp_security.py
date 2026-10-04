"""Security regression tests for Mortarium MCP execution boundaries."""

import pytest
from pydantic import BaseModel

from src.pharmaviyum.ai.mcp.registry import MCPToolRegistry
from src.pharmaviyum.ai.mcp.security import (
    validate_execution_policy,
    validate_tool_schema,
)


class SafeInput(BaseModel):
    product_id: int


class SqlInput(BaseModel):
    sql: str


class CommandInput(BaseModel):
    command: str


class EmptyOutput(BaseModel):
    ok: bool


@pytest.mark.unit
def test_forbids_arbitrary_sql_schema():
    with pytest.raises(ValueError, match="forbidden execution input"):
        validate_tool_schema(SqlInput.model_json_schema())


@pytest.mark.unit
def test_forbids_arbitrary_command_schema():
    with pytest.raises(ValueError, match="forbidden execution input"):
        validate_tool_schema(CommandInput.model_json_schema())


@pytest.mark.unit
def test_write_tool_requires_confirmation_at_registration():
    with pytest.raises(
        ValueError, match="must require explicit pharmacist/user confirmation"
    ):
        validate_execution_policy("write", False)


@pytest.mark.unit
def test_safe_read_schema_is_allowed():
    validate_tool_schema(SafeInput.model_json_schema())


@pytest.mark.unit
def test_registry_rejects_unconfirmed_write_tool():
    registry = MCPToolRegistry()
    with pytest.raises(ValueError, match="must require explicit pharmacist/user confirmation"):
        registry.tool(
            name="unsafe_write",
            description="Test write tool",
            input_schema=SafeInput,
            output_schema=EmptyOutput,
            execution_class="write",
            requires_pharmacist_confirmation=False,
        )
