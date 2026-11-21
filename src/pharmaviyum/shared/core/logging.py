"""
Structured JSON logging with correlation IDs.

Best practice 2026: JSON logs for aggregation (ELK, Loki, CloudWatch),
correlation IDs for distributed tracing across modules.
"""

import json
import logging
import sys
from datetime import datetime, timezone

from .config import settings


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add correlation ID if available
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id

        # Add module name for tracing
        if hasattr(record, "module_name"):
            log_data["module"] = record.module_name

        # Add user ID if available
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        # Add extra fields
        if hasattr(record, "extra_data") and record.extra_data:
            log_data["extra"] = record.extra_data

        # Add exception info
        if record.exc_info and record.exc_info[0]:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
            }

        return json.dumps(log_data, ensure_ascii=False)


def setup_logging() -> None:
    """Setup structured logging for the application."""
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    root_logger.addHandler(handler)

    # Reduce noise from third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


# Initialize logging
setup_logging()
logger = logging.getLogger("pharmaviyum")
