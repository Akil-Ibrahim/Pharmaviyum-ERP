"""
Notification tasks for patient communication
Best practice 2026: Multi-channel (Zalo/LINE/WhatsApp) with templates
"""

from typing import Any, Optional

from src.pharmaviyum.core.logging import get_logger
from src.pharmaviyum.workers.base import BaseTask, RetryConfig
from src.pharmaviyum.workers.queues import TaskQueue

logger = get_logger(__name__)


class SendPatientNotificationTask(BaseTask):
    """
    Send notification to patient via preferred channel

    Channels:
    - Zalo (Vietnam)
    - LINE (Thailand)
    - WhatsApp (Indonesia, Malaysia, Singapore)
    - Facebook Messenger (Philippines)
    - SMS (fallback)
    - Email (fallback)
    """

    name = "send_patient_notification"
    queue = TaskQueue.NOTIFICATIONS.value
    timeout_seconds = 30
    retry_config = RetryConfig(max_attempts=3, base_delay_seconds=2.0)

    async def execute(
        self,
        patient_id: int,
        pharmacy_id: int,
        template_name: str,
        template_data: dict[str, Any],
        channel: Optional[str] = None,
        language: str = "vi",
    ) -> dict:
        """
        Send notification to patient

        Args:
            patient_id: Patient ID
            pharmacy_id: Authorized pharmacy tenant ID
            template_name: Notification template name
            template_data: Template variables
            channel: Override notification channel (optional)
            language: Language code (default: vi)

        Returns:
            Notification result with message_id
        """
        # Import here to avoid circular imports
        from src.pharmaviyum.core.database import async_session
        from src.pharmaviyum.models.patients import Patient

        # Fetch patient
        async with async_session() as session:
            result = await session.execute(
                Patient.__table__.select().where(
                    Patient.id == patient_id,
                    Patient.pharmacy_id == pharmacy_id,
                )
            )
            patient = result.first()

            if not patient:
                raise ValueError(f"Patient {patient_id} not found")

            # Determine channel
            target_channel = channel or patient.preferred_notification_channel

            # Render template
            message = self._render_template(template_name, template_data, language)

            # Send via appropriate channel
            if target_channel == "zalo":
                result = await self._send_zalo(patient.phone, message)
            elif target_channel == "line":
                result = await self._send_line(patient.phone, message)
            elif target_channel == "whatsapp":
                result = await self._send_whatsapp(patient.phone, message)
            elif target_channel == "messenger":
                result = await self._send_messenger(patient.phone, message)
            elif target_channel == "sms":
                result = await self._send_sms(patient.phone, message)
            elif target_channel == "email":
                result = await self._send_email(patient.email, message)
            else:
                raise ValueError(f"Unsupported channel: {target_channel}")

        return {
            "patient_id": patient_id,
            "channel": target_channel,
            "template": template_name,
            "message_id": result.get("message_id"),
            "status": "sent",
        }

    def _render_template(
        self,
        template_name: str,
        data: dict[str, Any],
        language: str,
    ) -> str:
        """Render notification template with variables"""
        # Template registry (expand as needed)
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

        # Simple variable substitution
        for key, value in data.items():
            template = template.replace(f"{{{key}}}", str(value))

        return template

    async def _send_zalo(self, phone: str, message: str) -> dict:
        """Send via Zalo API"""
        # TODO: Implement Zalo API integration
        logger.info("Sending Zalo message")
        return {"message_id": f"zalo_{__import__('uuid').uuid4()}"}

    async def _send_line(self, phone: str, message: str) -> dict:
        """Send via LINE API"""
        # TODO: Implement LINE API integration
        logger.info("Sending LINE message")
        return {"message_id": f"line_{__import__('uuid').uuid4()}"}

    async def _send_whatsapp(self, phone: str, message: str) -> dict:
        """Send via WhatsApp Business API"""
        # TODO: Implement WhatsApp API integration
        logger.info("Sending WhatsApp message")
        return {"message_id": f"wa_{__import__('uuid').uuid4()}"}

    async def _send_messenger(self, phone: str, message: str) -> dict:
        """Send via Facebook Messenger"""
        # TODO: Implement Messenger API integration
        logger.info("Sending Messenger message")
        return {"message_id": f"msg_{__import__('uuid').uuid4()}"}

    async def _send_sms(self, phone: str, message: str) -> dict:
        """Send via SMS (fallback)"""
        # TODO: Implement SMS gateway integration
        logger.info("Sending SMS")
        return {"message_id": f"sms_{__import__('uuid').uuid4()}"}

    async def _send_email(self, email: str, message: str) -> dict:
        """Send via Email (fallback)"""
        # TODO: Implement email integration
        logger.info("Sending email")
        return {"message_id": f"email_{__import__('uuid').uuid4()}"}
