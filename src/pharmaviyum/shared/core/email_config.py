"""Backward-compatible exports for the centralized email configuration."""

from src.pharmaviyum.core.config import Settings as EmailSettings
from src.pharmaviyum.core.config import settings as email_settings

__all__ = ["EmailSettings", "email_settings"]
