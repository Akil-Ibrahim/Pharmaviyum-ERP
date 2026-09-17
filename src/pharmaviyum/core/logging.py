"""
Structured logging with JSON format
Best practice 2026: JSON logs for log aggregation (ELK, Loki, CloudWatch)
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from src.pharmaviyum.core.config import settings


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "extra_data") and record.extra_data:
            log_data["extra"] = record.extra_data

        if record.exc_info:
            exception_type = record.exc_info[0] or Exception
            exception_value = record.exc_info[1]
            log_data["exception"] = {
                "type": exception_type.__name__,
                "message": str(exception_value),
                "traceback": self.formatException(record.exc_info),
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

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """Logger adapter for adding context (correlation_id, user_id)."""

    def process(self, msg: str, kwargs: Any) -> tuple[str, Any]:
        """Add context to log messages."""
        extra = dict(kwargs.get("extra") or {})
        context = dict(self.extra or {})

        for key in ("correlation_id", "user_id"):
            if key in context:
                extra[key] = context[key]

        kwargs["extra"] = extra
        return msg, kwargs


logger = get_logger("pharmaviyum")
