"""Trusted execution context for MCP tools.

The context is injected by the authenticated application boundary and is
intentionally kept out of LLM-visible tool schemas.
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Literal

from .registry import UserRole

PatientAccessPurpose = Literal[
    "dispensing_review", "medication_reconciliation", "patient_request"
]


@dataclass(frozen=True)
class MCPAuthorizationContext:
    """Authenticated identity and tenant scope for one MCP execution."""

    user_id: int
    pharmacy_id: int
    user_role: UserRole
    selected_patient_id: int | None = None
    purpose: PatientAccessPurpose | None = None
    request_id: str | None = None

    def __post_init__(self) -> None:
        """Reject invalid identity and tenant values at the trust boundary."""
        if type(self.user_id) is not int or self.user_id <= 0:
            raise ValueError("MCP context requires a positive authenticated user_id")
        if type(self.pharmacy_id) is not int or self.pharmacy_id <= 0:
            raise ValueError("MCP context requires a positive pharmacy_id")
        if self.selected_patient_id is not None and (
            type(self.selected_patient_id) is not int or self.selected_patient_id <= 0
        ):
            raise ValueError(
                "MCP context selected_patient_id must be a positive integer or None"
            )
        if self.purpose is not None and self.selected_patient_id is None:
            raise ValueError("MCP context purpose requires a selected patient")
        if self.purpose is not None and self.purpose not in (
            "dispensing_review",
            "medication_reconciliation",
            "patient_request",
        ):
            raise ValueError("MCP context requires a recognized patient-access purpose")
        if self.request_id is not None and (
            not isinstance(self.request_id, str)
            or not self.request_id.strip()
            or len(self.request_id) > 128
        ):
            raise ValueError("MCP context request_id must contain 1-128 characters")
        if not isinstance(self.user_role, str) or self.user_role not in (
            "patient",
            "pharmacist",
            "admin",
            "system",
        ):
            raise ValueError("MCP context requires a recognized user role")


_current_context: ContextVar[MCPAuthorizationContext | None] = ContextVar(
    "mcp_authorization_context", default=None
)


def set_mcp_context(context: MCPAuthorizationContext) -> Token:
    """Set trusted MCP context for the current async execution scope."""
    return _current_context.set(context)


def reset_mcp_context(token: Token) -> None:
    """Restore the previous MCP context."""
    _current_context.reset(token)


def require_mcp_context() -> MCPAuthorizationContext:
    """Return trusted context or fail closed when called outside an authorized request."""
    context = _current_context.get()
    if context is None:
        raise PermissionError("MCP tenant authorization context is required")
    return context
