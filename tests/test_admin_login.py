import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import ValidationError

from src.pharmaviyum.api.v1.auth import settings, token
from src.pharmaviyum.config import Settings


def test_production_accepts_documented_secret_key():
    configured = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        SECRET_KEY="s" * 32,
        API_SECRET_KEY=None,
    )

    assert configured.API_SECRET_KEY == "s" * 32


def test_production_rejects_missing_jwt_secret():
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            SECRET_KEY=None,
            API_SECRET_KEY=None,
        )


def test_bootstrap_admin_password_is_not_enabled_by_default():
    configured = Settings(
        _env_file=None,
        ENVIRONMENT="development",
        SECRET_KEY=None,
        API_SECRET_KEY=None,
        ADMIN_PASSWORD=None,
    )

    assert configured.ADMIN_PASSWORD is None


def test_default_admin_credentials_are_rejected(monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_PASSWORD", None)

    async def assert_rejected():
        with patch(
            "src.pharmaviyum.api.v1.auth._get_user_by_username_or_email",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await token(
                    OAuth2PasswordRequestForm(username="admin", password="admin"),
                    AsyncMock(),
                )

        assert exc_info.value.status_code == 401

    asyncio.run(assert_rejected())
