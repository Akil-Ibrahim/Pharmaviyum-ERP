"""Regression tests for secure account-creation email content."""

from src.pharmaviyum.modules.auth import utils


def test_new_account_email_uses_password_setup_link(monkeypatch) -> None:
    monkeypatch.setattr(
        utils.settings, "APP_URL", "https://app.example.test", raising=False
    )

    email = utils.generate_new_account_email(
        email_to="pharmacist@example.test",
        username="pharmacist@example.test",
        setup_token="one-time-setup-token",
    )

    assert email.subject == "Welcome to Pharmaviyum CRM"
    assert "https://app.example.test/reset-password?token=one-time-setup-token" in (
        email.html_content
    )
    assert "Set Password" in email.html_content
    assert "Password:</strong>" not in email.html_content


def test_new_account_email_escapes_untrusted_username() -> None:
    email = utils.generate_new_account_email(
        email_to="pharmacist@example.test",
        username='<img src=x onerror="alert(1)">',
        setup_token="one-time-setup-token",
    )

    assert '<img src=x onerror="alert(1)">' not in email.html_content
    assert "&lt;img" in email.html_content
