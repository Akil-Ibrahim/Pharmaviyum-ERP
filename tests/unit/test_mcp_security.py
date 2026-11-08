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


class NestedInput(BaseModel):
    payload: SafeInput


class EmptyOutput(BaseModel):
    ok: bool


@pytest.mark.unit
def test_forbids_arbitrary_sql_schema() -> None:
    with pytest.raises(ValueError, match="forbidden execution input"):
        validate_tool_schema(SqlInput.model_json_schema())


@pytest.mark.unit
def test_forbids_arbitrary_command_schema() -> None:
    with pytest.raises(ValueError, match="forbidden execution input"):
        validate_tool_schema(CommandInput.model_json_schema())


@pytest.mark.unit
def test_write_tool_requires_confirmation_at_registration() -> None:
    with pytest.raises(
        ValueError,
        match="must require explicit pharmacist/user confirmation",
    ):
        validate_execution_policy("write", False)


@pytest.mark.unit
def test_safe_read_schema_is_allowed() -> None:
    validate_tool_schema(SafeInput.model_json_schema())


@pytest.mark.unit
def test_nested_schema_is_allowed() -> None:
    validate_tool_schema(NestedInput.model_json_schema())


@pytest.mark.unit
def test_registry_rejects_unconfirmed_write_tool() -> None:
    registry = MCPToolRegistry()

    with pytest.raises(
        ValueError,
        match="must require explicit pharmacist/user confirmation",
    ):
        registry.tool(
            name="unsafe_write",
            description="Test write tool",
            input_schema=SafeInput,
            output_schema=EmptyOutput,
            execution_class="write",
            requires_pharmacist_confirmation=False,
        )


@pytest.mark.asyncio
async def test_write_tool_fails_closed_without_trusted_approval_verifier() -> None:
    from src.pharmaviyum.ai.mcp.context import (
        MCPAuthorizationContext,
        reset_mcp_context,
        set_mcp_context,
    )

    registry = MCPToolRegistry()

    @registry.tool(
        name="confirmed_write",
        description="A write operation that requires pharmacist approval",
        input_schema=SafeInput,
        output_schema=EmptyOutput,
        execution_class="write",
        requires_pharmacist_confirmation=True,
        required_roles=["pharmacist"],
    )
    async def confirmed_write(data: SafeInput) -> EmptyOutput:
        return EmptyOutput(ok=True)

    token = set_mcp_context(
        MCPAuthorizationContext(user_id=10, pharmacy_id=20, user_role="pharmacist")
    )
    try:
        with pytest.raises(PermissionError, match="approval workflow"):
            await registry.call_tool(
                "confirmed_write",
                {"product_id": 5},
                user_role="pharmacist",
                user_id=10,
                pharmacy_id=20,
            )
    finally:
        reset_mcp_context(token)


@pytest.mark.asyncio
async def test_registry_rejects_caller_supplied_identity_mismatch() -> None:
    from src.pharmaviyum.ai.mcp.context import (
        MCPAuthorizationContext,
        reset_mcp_context,
        set_mcp_context,
    )

    registry = MCPToolRegistry()

    @registry.tool(
        name="patient_read",
        description="A scoped read operation",
        input_schema=SafeInput,
        output_schema=EmptyOutput,
        required_roles=["patient"],
    )
    async def patient_read(data: SafeInput) -> EmptyOutput:
        return EmptyOutput(ok=True)

    token = set_mcp_context(
        MCPAuthorizationContext(user_id=10, pharmacy_id=20, user_role="patient")
    )
    try:
        with pytest.raises(PermissionError, match="context mismatch"):
            await registry.call_tool(
                "patient_read",
                {"product_id": 5},
                user_role="pharmacist",
                user_id=10,
                pharmacy_id=20,
            )
    finally:
        reset_mcp_context(token)
