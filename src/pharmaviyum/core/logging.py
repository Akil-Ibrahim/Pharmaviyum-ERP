"""
Structured logging with JSON format
Best practice 2026: JSON logs for log aggregation (ELK, Loki, CloudWatch)
"""
import logging
import sys
import json
from datetime import datetime, timezone
from typing import Any, Optional
from src.pharmaviyum.core.config import settings


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
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
        
        # Add user ID if available
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        
        # Add request ID if available
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        # Add extra fields
        if hasattr(record, "extra_data") and record.extra_data:
            log_data["extra"] = record.extra_data
        
        # Add exception info
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }
        
        return json.dumps(log_data, ensure_ascii=False)


def setup_logging() -> None:
    """Setup structured logging for the application"""
    # Remove existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Create console handler with JSON formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    
    # Configure root logger
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    root_logger.addHandler(handler)
    
    # Reduce noise from third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name"""
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """Logger adapter for adding context (correlation_id, user_id)"""
    
    def process(self, msg: str, kwargs: Any) -> tuple[str, Any]:
        """Add context to log messages"""
        extra = kwargs.get("extra", {})
        
        # Add correlation ID from context
        if "correlation_id" in self.extra:
            extra["correlation_id"] = self.extra["correlation_id"]
        
        # Add user ID from context
        if "user_id" in self.extra:
            extra["user_id"] = self.extra["user_id"]
        
        kwargs["extra"] = extra
        return msg, kwargs
