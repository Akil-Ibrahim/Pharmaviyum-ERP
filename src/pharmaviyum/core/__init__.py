"""Core utilities and common exports for the application.

This module aggregates commonly used helpers so other parts of the
application can import them from a single place, e.g.:

	from src.pharmaviyum.core import settings, get_app_logger

Keep imports lightweight here to avoid heavy initialisation at package
import time. Only expose small helpers and configuration objects.
"""

from .config import settings
from .logging import configure_logging, get_app_logger
from .rate_limiter import limiter
from .security import get_current_user, TokenData
from .cors import add_cors_middleware
from .exceptions import (
	APIException,
	EntityNotFound,
	ValidationError,
	UnauthorizedError,
	ForbiddenError,
	ConflictError,
)
from .tenancy import get_tenant_from_request
from .feature_flags import is_feature_enabled
from .permissions import require_role

__all__ = [
	"settings",
	"configure_logging",
	"get_app_logger",
	"limiter",
	"get_current_user",
	"TokenData",
	"add_cors_middleware",
	"APIException",
	"EntityNotFound",
	"ValidationError",
	"UnauthorizedError",
	"ForbiddenError",
	"ConflictError",
	"get_tenant_from_request",
	"is_feature_enabled",
	"require_role",
]
