"""
Domain exceptions for consistent error handling across modules.

Each module can raise these exceptions, and they'll be handled
uniformly by the global exception handler in main.py.
"""
from typing import Optional, Any


class PharmaviyumException(Exception):
    """Base exception for all Pharmaviyum modules."""
    
    def __init__(
        self,
        message: str,
        code: str = "ERROR",
        status_code: int = 500,
        details: Optional[dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotFoundException(PharmaviyumException):
    """Resource not found."""
    
    def __init__(self, resource: str, identifier: Any = None):
        message = f"{resource} not found"
        if identifier is not None:
            message += f": {identifier}"
        super().__init__(message=message, code="NOT_FOUND", status_code=404)


class ValidationException(PharmaviyumException):
    """Validation error."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )


class ConflictException(PharmaviyumException):
    """Resource conflict (e.g., duplicate)."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409,
            details=details,
        )


class UnauthorizedException(PharmaviyumException):
    """Unauthorized access."""
    
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message=message, code="UNAUTHORIZED", status_code=401)


class ForbiddenException(PharmaviyumException):
    """Forbidden access."""
    
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message=message, code="FORBIDDEN", status_code=403)
