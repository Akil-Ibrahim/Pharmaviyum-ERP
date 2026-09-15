"""
Global Exception Handling for FastAPI.

Best practice 2026:
- Consistent JSON error response format
- No stack trace leakage to clients in production
- Specific handlers for domain-specific exceptions
"""

from __future__ import annotations

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.pharmaviyum.core.logging import logger


class PharmaviyumAPIError(Exception):
    """Base exception for Pharmaviyum API."""

    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = 500,
        details: dict | None = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class AgentExecutionError(PharmaviyumAPIError):
    """Raised when the AI agent fails to execute."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, "AGENT_EXECUTION_FAILED", 500, details)


class ToolAccessDeniedError(PharmaviyumAPIError):
    """Raised when a user lacks permissions for an MCP tool."""

    def __init__(self, tool_name: str, required_role: str):
        super().__init__(
            f"Access denied to tool: {tool_name}",
            "TOOL_ACCESS_DENIED",
            403,
            {"tool": tool_name, "required_role": required_role},
        )


async def pharmaviyum_api_error_handler(request: Request, exc: PharmaviyumAPIError):
    """Handler for custom domain exceptions."""
    logger.error(
        f"API Error: {exc.code} - {exc.message}",
        extra={
            "request_id": getattr(request.state, "request_id", "unknown"),
            "details": exc.details,
        },
        exc_info=True,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError | ValidationError
):
    """Handler for Pydantic/FastAPI validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request payload",
                "details": exc.errors(),
            }
        },
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Fallback handler for unexpected errors (prevents stack trace leakage)."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        f"Unhandled exception: {exc}",
        extra={"request_id": request_id},
        exc_info=True,
    )

    # In production, never expose str(exc) to the client
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please contact support.",
                "request_id": request_id,  # Helpful for support to look up logs
            }
        },
    )
