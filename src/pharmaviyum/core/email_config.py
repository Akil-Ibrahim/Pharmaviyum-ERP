"""Email configuration for different environments."""
from pydantic_settings import BaseSettings


class EmailSettings(BaseSettings):
    SMTP_HOST: str = "mailpit"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM: str = "noreply@pharmaviyum.com"
    EMAILS_ENABLED: bool = True
    
    model_config = {"env_file": ".env"}


email_settings = EmailSettings()
