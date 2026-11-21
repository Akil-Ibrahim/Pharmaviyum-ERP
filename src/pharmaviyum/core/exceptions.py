"""
Global exception handlers
Best practice 2026: Consistent error responses across all endpoints
"""

from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.pharmaviyum.core.logging import get_logger

logger = get_logger(__name__)


class PharmaviyumException(Exception):
    """Base exception for Pharmaviyum CRM"""

    def __init__(
        self,
        message: str,
        code: str = "ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        """Initialize exception"""
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotFoundException(PharmaviyumException):
    """Resource not found exception"""

    def __init__(self, resource: str, id: int | None = None):
        """Initialize not found exception"""
        message = f"{resource} not found"
        if id:
            message += f" with id {id}"

        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
        )


class ValidationException(PharmaviyumException):
    """Validation error exception"""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize validation exception"""
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )


class ConflictException(PharmaviyumException):
    """Resource conflict exception (duplicate, etc)"""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        """Initialize conflict exception"""
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409,
            details=details,
        )


class UnauthorizedException(PharmaviyumException):
    """Unauthorized access exception"""

    def __init__(self, message: str = "Unauthorized"):
        """Initialize unauthorized exception"""
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=401,
        )


class ForbiddenException(PharmaviyumException):
    """Forbidden access exception"""

    def __init__(self, message: str = "Forbidden"):
        """Initialize forbidden exception"""
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403,
        )


async def pharmaviyum_exception_handler(
    request: Request,
    exc: PharmaviyumException,
) -> JSONResponse:
    """Handle PharmaviyumException"""
    logger.error(
        f"PharmaviyumException: {exc.message}",
        extra={
            "code": exc.code,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "errors": [
                {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            ],
        },
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle Pydantic validation errors"""
    errors = []

    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append(
            {
                "code": "VALIDATION_ERROR",
                "message": error["msg"],
                "field": field,
                "type": error["type"],
            }
        )

    logger.warning(
        f"Validation error: {len(errors)} errors",
        extra={
            "errors": errors,
            "path": request.url.path,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "errors": errors,
        },
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """Handle HTTP exceptions"""
    logger.warning(
        f"HTTPException: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "errors": [
                {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                }
            ],
        },
    )


async def integrity_error_handler(
    request: Request,
    exc: IntegrityError,
) -> JSONResponse:
    """Handle database integrity errors (unique constraint, etc)"""
    error_msg = str(exc.orig)

    # Try to extract meaningful error message
    if "unique constraint" in error_msg.lower():
        message = "Resource already exists (duplicate entry)"
        code = "DUPLICATE_ENTRY"
    elif "foreign key constraint" in error_msg.lower():
        message = "Referenced resource does not exist"
        code = "FOREIGN_KEY_VIOLATION"
    else:
        message = "Database integrity error"
        code = "INTEGRITY_ERROR"

    logger.error(
        f"IntegrityError: {error_msg}",
        extra={
            "path": request.url.path,
            "error": error_msg,
        },
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "success": False,
            "errors": [
                {
                    "code": code,
                    "message": message,
                }
            ],
        },
    )


async def sqlalchemy_error_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    """Handle generic SQLAlchemy errors"""
    logger.error(
        f"SQLAlchemyError: {exc}",
        extra={"path": request.url.path},
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "errors": [
                {
                    "code": "DATABASE_ERROR",
                    "message": "Database error occurred",
                }
            ],
        },
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unhandled exceptions"""
    logger.error(
        f"Unhandled exception: {exc}",
        extra={"path": request.url.path},
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "errors": [
                {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                }
            ],
        },
    )
