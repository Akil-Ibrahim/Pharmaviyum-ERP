"""
Notification tasks for patient communication
Best practice 2026: Multi-channel (Zalo/LINE/WhatsApp) with templates
"""

from typing import Any, Optional, cast

from sqlalchemy import select

from src.pharmaviyum.core.logging import get_logger
from src.pharmaviyum.workers.base import BaseTask, RetryConfig
from src.pharmaviyum.workers.queues import TaskQueue

logger = get_logger(__name__)


class SendPatientNotificationTask(BaseTask):
    """Send notification to patient via preferred channel."""

    name = "send_patient_notification"
    queue = TaskQueue.NOTIFICATIONS.value
    timeout_seconds = 30
    retry_config = RetryConfig(max_attempts=3, base_delay_seconds=2.0)

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        patient_id = cast(int, kwargs["patient_id"])
        pharmacy_id = cast(int, kwargs["pharmacy_id"])
        template_name = cast(str, kwargs["template_name"])
        template_data = cast(dict[str, Any], kwargs["template_data"])
        channel = cast(Optional[str], kwargs.get("channel"))
        language = cast(str, kwargs.get("language", "vi"))

        from src.pharmaviyum.core.database import async_session
        from src.pharmaviyum.models.patients import Patient

        async with async_session() as session:
            result = await session.execute(
                select(Patient).where(
                    Patient.id == patient_id,
                    Patient.pharmacy_id == pharmacy_id,
                )
            )
            patient = result.scalar_one_or_none()

            if patient is None:
                raise ValueError(f"Patient {patient_id} not found")

            target_channel = channel or patient.preferred_notification_channel
            message = self._render_template(template_name, template_data, language)

            if target_channel == "zalo":
                send_result = await self._send_zalo(patient.phone, message)
            elif target_channel == "line":
                send_result = await self._send_line(patient.phone, message)
            elif target_channel == "whatsapp":
                send_result = await self._send_whatsapp(patient.phone, message)
            elif target_channel == "messenger":
                send_result = await self._send_messenger(patient.phone, message)
            elif target_channel == "sms":
                send_result = await self._send_sms(patient.phone, message)
            elif target_channel == "email":
                send_result = await self._send_email(patient.email, message)
            else:
                raise ValueError(f"Unsupported channel: {target_channel}")

        return {
            "patient_id": patient_id,
            "channel": target_channel,
            "template": template_name,
            "message_id": send_result.get("message_id"),
            "status": "sent",
        }

    def _render_template(
        self, template_name: str, data: dict[str, Any], language: str
    ) -> str:
        templates = {
            "medication_reminder": {
                "vi": "🔔 Đã đến giờ uống {medication_name} {dosage}. Nhắn 'OK' để xác nhận.",
                "en": "🔔 Time to take {medication_name} {dosage}. Reply 'OK' to confirm.",
            },
            "order_ready": {
                "vi": "✅ Đơn hàng #{order_id} đã sẵn sàng. Vui lòng đến lấy tại {pharmacy_address}.",
                "en": "✅ Order #{order_id} is ready. Please pick up at {pharmacy_address}.",
            },
            "prescription_refill": {
                "vi": "💊 Đơn thuốc của bạn sắp hết hạn. Đặt lịch tái khám hoặc gia hạn đơn.",
                "en": "💊 Your prescription is expiring soon. Schedule a follow-up or renew.",
            },
            "loyalty_reward": {
                "vi": "🎉 Chúc mừng! Bạn đã đạt hạng {tier} với {points} điểm thưởng.",
                "en": "🎉 Congratulations! You've reached {tier} tier with {points} reward points.",
            },
        }
        template_dict = templates.get(template_name, {})
        template = template_dict.get(language, template_dict.get("en", ""))
        if not template:
            raise ValueError(f"Template not found: {template_name}")
        for key, value in data.items():
            template = template.replace(f"{{{key}}}", str(value))
        return template

    async def _send_zalo(self, phone: str, message: str) -> dict[str, Any]:
        logger.info("Sending Zalo message")
        return {"message_id": f"zalo_{__import__('uuid').uuid4()}"}

    async def _send_line(self, phone: str, message: str) -> dict[str, Any]:
        logger.info("Sending LINE message")
        return {"message_id": f"line_{__import__('uuid').uuid4()}"}

    async def _send_whatsapp(self, phone: str, message: str) -> dict[str, Any]:
        logger.info("Sending WhatsApp message")
        return {"message_id": f"wa_{__import__('uuid').uuid4()}"}

    async def _send_messenger(self, phone: str, message: str) -> dict[str, Any]:
        logger.info("Sending Messenger message")
        return {"message_id": f"msg_{__import__('uuid').uuid4()}"}

    async def _send_sms(self, phone: str, message: str) -> dict[str, Any]:
        logger.info("Sending SMS")
        return {"message_id": f"sms_{__import__('uuid').uuid4()}"}

    async def _send_email(self, email: str, message: str) -> dict[str, Any]:
        logger.info("Sending email")
        return {"message_id": f"email_{__import__('uuid').uuid4()}"}
