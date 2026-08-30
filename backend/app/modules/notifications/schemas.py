"""
Notification schemas using Pydantic v2 Discriminated Unions.

Discriminators enable:
- Type-safe polymorphic request validation
- Automatic schema selection based on 'type' field
- Better OpenAPI documentation
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Literal, Union, Annotated


class EmailNotification(BaseModel):
    """Email notification schema."""
    type: Literal["email"] = Field(default="email")
    to: EmailStr
    subject: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1)


class SMSNotification(BaseModel):
    """SMS notification schema."""
    type: Literal["sms"] = Field(default="sms")
    phone: str = Field(..., pattern=r"^\+?[0-9]{10,15}$")
    message: str = Field(..., min_length=1, max_length=160)


class ZaloNotification(BaseModel):
    """Zalo notification schema (Vietnam-specific)."""
    type: Literal["zalo"] = Field(default="zalo")
    zalo_user_id: str = Field(..., min_length=1)
    template_name: str
    template_data: dict


class LINENotification(BaseModel):
    """LINE notification schema (Thailand-specific)."""
    type: Literal["line"] = Field(default="line")
    line_user_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


# Discriminated union: routes to correct schema based on 'type' field
Notification = Annotated[
    Union[EmailNotification, SMSNotification, ZaloNotification, LINENotification],
    Field(discriminator="type"),
]


class SendNotificationRequest(BaseModel):
    """Request to send a notification."""
    notification: Notification = Field(..., description="Notification to send")
    send_immediately: bool = Field(default=True)


class NotificationResponse(BaseModel):
    """Response after sending notification."""
    id: str
    type: str
    status: str
    sent_at: str
