"""Production email configuration validation tests."""

import pytest

from src.pharmaviyum.core.config import Environment, Settings


def test_production_email_requires_tls() -> None:
    with pytest.raises(ValueError, match="requires SMTP TLS"):
        Settings(
            ENVIRONMENT=Environment.PRODUCTION,
            SECRET_KEY="s" * 32,
            EMAILS_ENABLED=True,
            APP_URL="https://pharmaviyum.example",
            SMTP_HOST="smtp.example.test",
            SMTP_STARTTLS=False,
            SMTP_SSL=False,
        )


def test_production_email_requires_https_app_url() -> None:
    with pytest.raises(ValueError, match="APP_URL must use HTTPS"):
        Settings(
            ENVIRONMENT=Environment.PRODUCTION,
            SECRET_KEY="s" * 32,
            EMAILS_ENABLED=True,
            APP_URL="http://pharmaviyum.example",
            SMTP_HOST="smtp.example.test",
            SMTP_STARTTLS=True,
            SMTP_SSL=False,
        )


def test_production_email_accepts_tls_configuration() -> None:
    settings = Settings(
        ENVIRONMENT=Environment.PRODUCTION,
        SECRET_KEY="s" * 32,
        EMAILS_ENABLED=True,
        APP_URL="https://pharmaviyum.example",
        SMTP_HOST="smtp.example.test",
        SMTP_STARTTLS=True,
        SMTP_SSL=False,
    )

    assert settings.SMTP_HOST == "smtp.example.test"
    assert settings.APP_URL.startswith("https://")
