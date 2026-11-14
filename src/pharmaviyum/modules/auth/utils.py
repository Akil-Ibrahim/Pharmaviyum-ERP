"""Authentication utilities for email templates and password recovery."""

import asyncio
import html
import logging
import smtplib
import ssl
from email.message import EmailMessage
from dataclasses import dataclass
from datetime import datetime

from ...core.security import create_password_reset_token, decode_password_reset_token
from ...core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class EmailData:
    """Container for email data."""

    html_content: str
    subject: str


def _send_email_sync(email_to: str, subject: str, html_content: str) -> None:
    """Deliver one HTML email using the configured SMTP server."""
    smtp_host = settings.SMTP_HOST
    if not smtp_host:
        raise RuntimeError("SMTP_HOST must be configured when email delivery is enabled")
    if bool(settings.SMTP_USER) != bool(settings.SMTP_PASSWORD):
        raise RuntimeError("SMTP_USER and SMTP_PASSWORD must be configured together")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.EMAILS_FROM
    message["To"] = email_to
    message.set_content("This message contains HTML content. Please use an HTML-capable email client.")
    message.add_alternative(html_content, subtype="html")

    timeout = settings.SMTP_TIMEOUT_SECONDS
    if settings.SMTP_SSL:
        with smtplib.SMTP_SSL(
            smtp_host,
            settings.SMTP_PORT,
            timeout=timeout,
            context=ssl.create_default_context(),
        ) as smtp:
            if settings.SMTP_USER:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD or "")
            smtp.send_message(message)
        return

    with smtplib.SMTP(smtp_host, settings.SMTP_PORT, timeout=timeout) as smtp:
        if settings.SMTP_STARTTLS:
            smtp.starttls(context=ssl.create_default_context())
        if settings.SMTP_USER:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD or "")
        smtp.send_message(message)


async def send_email(email_to: str, subject: str, html_content: str) -> None:
    """Send email without blocking the FastAPI event loop."""
    try:
        await asyncio.to_thread(_send_email_sync, email_to, subject, html_content)
    except Exception:
        logger.exception("Email delivery failed for %s", subject)
        raise

def generate_email_logo_and_footer() -> tuple[str, str]:
    """Generate common email header and footer HTML."""
    app_name = settings.APP_NAME
    logo_html = f"""
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="color: #1a73e8; margin: 0;">💊 {html.escape(app_name)}</h1>
    </div>
    """
    footer_html = f"""
    <div style="text-align: center; padding: 20px; color: #666;
                font-size: 12px; border-top: 1px solid #eee; margin-top: 30px;">
        <p>© {datetime.now().year} {html.escape(app_name)}. All rights reserved.</p>
        <p>This is an automated message, please do not reply.</p>
    </div>
    """
    return logo_html, footer_html


def generate_new_account_email(
    email_to: str, username: str, setup_token: str
) -> EmailData:
    """Generate a welcome email with a one-time password setup link.

    Never include an account password in email. The setup token is short-lived
    and is consumed by the existing password-reset endpoint.
    """
    logo, footer = generate_email_logo_and_footer()
    app_url = settings.APP_URL.rstrip("/")
    setup_url = f"{app_url}/reset-password?token={setup_token}"
    subject = f"Welcome to {settings.APP_NAME}"
    safe_username = html.escape(username)
    safe_setup_url = html.escape(setup_url, quote=True)
    html_content = f"""
    <!DOCTYPE html>
    <html><body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px;">
      <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px;">
        {logo}
        <h2 style="color: #333;">Welcome, {safe_username}!</h2>
        <p style="color: #666; line-height: 1.6;">Your account has been created. Use the secure link below to set your password.</p>
        <div style="text-align: center; margin: 30px 0;">
          <a href="{safe_setup_url}" style="display: inline-block; background: #1a73e8; color: white; padding: 12px 32px; text-decoration: none; border-radius: 6px; font-weight: bold;">Set Password</a>
        </div>
        <p style="color: #666; line-height: 1.6; font-size: 14px;">This link expires in 48 hours and can only be used once. If you did not expect this account, contact your administrator.</p>
        {footer}
      </div>
    </body></html>
    """
    return EmailData(html_content=html_content, subject=subject)


def generate_password_reset_token(email: str) -> str:
    """Generate a 48-hour password-reset token."""
    return create_password_reset_token(email)


def verify_password_reset_token(token: str) -> str | None:
    """Verify a password-reset token and return its email subject."""
    payload = decode_password_reset_token(token)
    if not payload:
        return None
    subject = payload.get("sub")
    return subject if isinstance(subject, str) else None


def generate_reset_password_email(email_to: str, email: str, token: str) -> EmailData:
    """Generate a password-reset email containing the one-time token."""
    logo, footer = generate_email_logo_and_footer()
    app_url = settings.APP_URL.rstrip("/")
    reset_url = f"{app_url}/reset-password?token={token}"
    subject = f"Password Recovery - {settings.APP_NAME}"
    html_content = f"""
    <!DOCTYPE html>
    <html><body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px;">
      <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px;">
        {logo}
        <h2 style="color: #333;">Password Recovery</h2>
        <p style="color: #666; line-height: 1.6;">Hello {html.escape(email)},</p>
        <p style="color: #666; line-height: 1.6;">We received a request to reset your password.</p>
        <div style="text-align: center; margin: 30px 0;">
          <a href="{html.escape(reset_url, quote=True)}" style="display: inline-block; background: #1a73e8; color: white; padding: 12px 32px; text-decoration: none; border-radius: 6px; font-weight: bold;">Reset Password</a>
        </div>
        <p style="color: #666; line-height: 1.6; font-size: 14px;">This link will expire in 48 hours and can only be used once.</p>
        {footer}
      </div>
    </body></html>
    """
    return EmailData(html_content=html_content, subject=subject)
