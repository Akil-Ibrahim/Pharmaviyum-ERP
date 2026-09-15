"""Authentication utilities for email templates and password recovery."""

import logging
from dataclasses import dataclass
from datetime import datetime

from ...core.security import (create_password_reset_token,
                              decode_password_reset_token)
from ...shared.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class EmailData:
    """Container for email data."""

    html_content: str
    subject: str


def send_email(email_to: str, subject: str, html_content: str) -> None:
    """Send an email message through the configured provider abstraction."""
    logger.info("Sending email to %s: %s", email_to, subject)
    logger.debug("Email content preview: %s...", html_content[:100])


def generate_email_logo_and_footer() -> tuple[str, str]:
    """Generate common email header and footer HTML."""
    app_name = settings.APP_NAME
    logo_html = f"""
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="color: #1a73e8; margin: 0;">💊 {app_name}</h1>
    </div>
    """
    footer_html = f"""
    <div style="text-align: center; padding: 20px; color: #666;
                font-size: 12px; border-top: 1px solid #eee; margin-top: 30px;">
        <p>© {datetime.now().year} {app_name}. All rights reserved.</p>
        <p>This is an automated message, please do not reply.</p>
    </div>
    """
    return logo_html, footer_html


def generate_new_account_email(
    email_to: str, username: str, password: str
) -> EmailData:
    """Generate a welcome email for a newly created user."""
    logo, footer = generate_email_logo_and_footer()
    app_url = getattr(settings, "APP_URL", "http://localhost:3000")
    subject = f"Welcome to {settings.APP_NAME}"
    html_content = f"""
    <!DOCTYPE html>
    <html><body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px;">
      <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px;">
        {logo}
        <h2 style="color: #333;">Welcome, {username}!</h2>
        <p style="color: #666; line-height: 1.6;">Your account has been created. You can now login.</p>
        <div style="background: #f8f9fa; padding: 20px; border-radius: 6px; margin: 20px 0;">
          <p style="margin: 8px 0;"><strong>Login:</strong> {username}</p>
          <p style="margin: 8px 0;"><strong>Password:</strong> {password}</p>
        </div>
        <p style="color: #666; line-height: 1.6;"><strong>⚠️ Security:</strong> Please change your password after first login.</p>
        <div style="text-align: center; margin: 30px 0;">
          <a href="{app_url}/login" style="display: inline-block; background: #1a73e8; color: white; padding: 12px 32px; text-decoration: none; border-radius: 6px; font-weight: bold;">Login Now</a>
        </div>
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
    app_url = getattr(settings, "APP_URL", "http://localhost:3000")
    reset_url = f"{app_url}/reset-password?token={token}"
    subject = f"Password Recovery - {settings.APP_NAME}"
    html_content = f"""
    <!DOCTYPE html>
    <html><body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px;">
      <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px;">
        {logo}
        <h2 style="color: #333;">Password Recovery</h2>
        <p style="color: #666; line-height: 1.6;">Hello {email},</p>
        <p style="color: #666; line-height: 1.6;">We received a request to reset your password.</p>
        <div style="text-align: center; margin: 30px 0;">
          <a href="{reset_url}" style="display: inline-block; background: #1a73e8; color: white; padding: 12px 32px; text-decoration: none; border-radius: 6px; font-weight: bold;">Reset Password</a>
        </div>
        <p style="color: #666; line-height: 1.6; font-size: 14px;">This link will expire in 48 hours and can only be used once.</p>
        {footer}
      </div>
    </body></html>
    """
    return EmailData(html_content=html_content, subject=subject)
