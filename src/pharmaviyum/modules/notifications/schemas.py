"""Notification schemas with Pydantic v2 Discriminated Unions."""
from pydantic import BaseModel, Field, EmailStr
from typing import Literal, Union, Annotated


class EmailNotification(BaseModel):
    type: Literal["email"] = Field(default="email")
    to: EmailStr
    subject: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1)


class SMSNotification(BaseModel):
    type: Literal["sms"] = Field(default="sms")
    phone: str = Field(..., pattern=r"^\+?[0-9]{10,15}$")
    message: str = Field(..., min_length=1, max_length=160)


class ZaloNotification(BaseModel):
    type: Literal["zalo"] = Field(default="zalo")
    zalo_user_id: str = Field(..., min_length=1)
    template_name: str
    template_data: dict


class LINENotification(BaseModel):
    type: Literal["line"] = Field(default="line")
    line_user_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


Notification = Annotated[
    Union[EmailNotification, SMSNotification, ZaloNotification, LINENotification],
    Field(discriminator="type"),
]


class SendNotificationRequest(BaseModel):
    notification: Notification
    send_immediately: bool = Field(default=True)


class NotificationResponse(BaseModel):
    id: str
    type: str
    status: str
    sent_at: str
