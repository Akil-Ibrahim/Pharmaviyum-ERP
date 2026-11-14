"""Tests for SMTP delivery and non-blocking email dispatch."""

import pytest
from email.message import EmailMessage
from typing import Any

from src.pharmaviyum.modules.auth import utils


@pytest.mark.asyncio
async def test_send_email_dispatches_delivery_to_worker_thread(monkeypatch) -> None:
    calls: list[tuple[str, str, str]] = []

    def fake_delivery(email_to: str, subject: str, html_content: str) -> None:
        calls.append((email_to, subject, html_content))

    monkeypatch.setattr(utils, "_send_email_sync", fake_delivery)

    await utils.send_email(
        "pharmacist@example.test",
        "Welcome",
        "<p>Set your password</p>",
    )

    assert calls == [
        (
            "pharmacist@example.test",
            "Welcome",
            "<p>Set your password</p>",
        )
    ]


def test_smtp_delivery_uses_starttls_and_authentication(monkeypatch) -> None:
    sent_messages: list[EmailMessage] = []

    class FakeSMTP:
        def __init__(self, host: str, port: int, timeout: int) -> None:
            assert host == "smtp.example.test"
            assert port == 587
            assert timeout == 10

        def __enter__(self) -> FakeSMTP:
            return self

        def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
            return None

        def starttls(self, context: Any) -> None:
            assert context is not None

        def login(self, username: str, password: str) -> None:
            assert username == "smtp-user"
            assert password == "smtp-password"

        def send_message(self, message: EmailMessage) -> None:
            sent_messages.append(message)

    monkeypatch.setattr(utils.settings, "SMTP_HOST", "smtp.example.test")
    monkeypatch.setattr(utils.settings, "SMTP_PORT", 587)
    monkeypatch.setattr(utils.settings, "SMTP_STARTTLS", True)
    monkeypatch.setattr(utils.settings, "SMTP_SSL", False)
    monkeypatch.setattr(utils.settings, "SMTP_USER", "smtp-user")
    monkeypatch.setattr(utils.settings, "SMTP_PASSWORD", "smtp-password")
    monkeypatch.setattr(utils.settings, "EMAILS_FROM", "noreply@example.test")
    monkeypatch.setattr(utils.smtplib, "SMTP", FakeSMTP)

    utils._send_email_sync(
        "pharmacist@example.test",
        "Password setup",
        "<p>Use the setup link</p>",
    )

    assert len(sent_messages) == 1
    assert sent_messages[0]["To"] == "pharmacist@example.test"
    assert sent_messages[0]["From"] == "noreply@example.test"
    assert sent_messages[0]["Subject"] == "Password setup"
