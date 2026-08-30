"""
Authentication utilities: email templates + password reset tokens.

Implements:
- Welcome email generation for new users
- Password reset token generation (JWT-based)
- Password reset token verification
- Email sending abstraction
"""
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from typing import Any
from jose import jwt
from ...shared.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class EmailData:
    """Container for email data."""
    html_content: str
    subject: str


def send_email(
    email_to: str,
    subject: str,
    html_content: str,
) -> None:
    """
    Send an email message.
    
    In production, integrate with:
    - SendGrid
    - AWS SES
    - Mailgun
    
    For development, use Mailpit (see Point 6).
    """
    logger.info(f"Sending email to {email_to}: {subject}")
    
    # TODO: Integrate real email provider
    # Example with SMTP:
    # import smtplib
    # from email.mime.text import MIMEText
    # ...
    
    # For now, just log (Mailpit will capture if configured)
    logger.debug(f"Email content preview: {html_content[:100]}...")


def generate_email_logo_and_footer() -> tuple[str, str]:
    """Generate common email header and footer HTML."""
    app_url = getattr(settings, 'APP_URL', 'http://localhost:3000')
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
    email_to: str,
    username: str,
    password: str,
) -> EmailData:
    """
    Generate welcome email for new user created by admin.
    
    Includes temporary password in email body.
    """
    logo, footer = generate_email_logo_and_footer()
    app_url = getattr(settings, 'APP_URL', 'http://localhost:3000')
    
    subject = f"Welcome to {settings.APP_NAME}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; 
                    border-radius: 8px; padding: 30px;">
            {logo}
            
            <h2 style="color: #333;">Welcome, {username}!</h2>
            
            <p style="color: #666; line-height: 1.6;">
                Your account has been created. You can now login with the following credentials:
            </p>
            
            <div style="background: #f8f9fa; padding: 20px; 
                        border-radius: 6px; margin: 20px 0;">
                <p style="margin: 8px 0;"><strong>Login:</strong> {username}</p>
                <p style="margin: 8px 0;"><strong>Password:</strong> {password}</p>
            </div>
            
            <p style="color: #666; line-height: 1.6;">
                <strong>⚠️ Security:</strong> Please change your password after first login.
            </p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{app_url}/login" 
                   style="display: inline-block; background: #1a73e8; color: white; 
                          padding: 12px 32px; text-decoration: none; 
                          border-radius: 6px; font-weight: bold;">
                    Login Now
                </a>
            </div>
            
            {footer}
        </div>
    </body>
    </html>
    """
    
    return EmailData(html_content=html_content, subject=subject)


def generate_password_reset_token(email: str) -> str:
    """
    Generate a JWT token for password reset.
    
    Token expires in 48 hours.
    Contains email in payload for verification.
    """
    delta = timedelta(hours=48)
    now = datetime.utcnow()
    expires = now + delta
    
    to_encode = {
        "exp": expires,
        "sub": email,
        "type": "password_reset",
        "iat": now,
    }
    
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def verify_password_reset_token(token: str) -> str | None:
    """
    Verify password reset token and extract email.
    
    Returns:
        Email address if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        
        # Verify token type
        if payload.get("type") != "password_reset":
            return None
        
        return payload.get("sub")
    except Exception:
        return None


def generate_reset_password_email(
    email_to: str,
    email: str,
    token: str,
) -> EmailData:
    """
    Generate password reset email with reset link.
    
    Link includes token as query parameter.
    """
    logo, footer = generate_email_logo_and_footer()
    app_url = getattr(settings, 'APP_URL', 'http://localhost:3000')
    
    reset_url = f"{app_url}/reset-password?token={token}"
    
    subject = f"Password Recovery - {settings.APP_NAME}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; 
                    border-radius: 8px; padding: 30px;">
            {logo}
            
            <h2 style="color: #333;">Password Recovery</h2>
            
            <p style="color: #666; line-height: 1.6;">
                Hello {email},
            </p>
            
            <p style="color: #666; line-height: 1.6;">
                We received a request to reset your password. 
                Click the button below to set a new password:
            </p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" 
                   style="display: inline-block; background: #1a73e8; color: white; 
                          padding: 12px 32px; text-decoration: none; 
                          border-radius: 6px; font-weight: bold;">
                    Reset Password
                </a>
            </div>
            
            <p style="color: #666; line-height: 1.6; font-size: 14px;">
                This link will expire in 48 hours.
            </p>
            
            <p style="color: #999; line-height: 1.6; font-size: 14px;">
                If you didn't request a password reset, you can safely ignore this email.
            </p>
            
            {footer}
        </div>
    </body>
    </html>
    """
    
    return EmailData(html_content=html_content, subject=subject)
