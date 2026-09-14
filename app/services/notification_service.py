import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import asyncio
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

class NotificationService:
    def __init__(self):
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.smtp_from_email = settings.smtp_from_email
        self.smtp_to_email = settings.smtp_to_email
        self.webhook_url = settings.webhook_url

    async def send_alert_notification(self, alert_id: str, severity: str, message: str):
        """Send notifications for an alert using all configured channels."""
        tasks = []
        if self._is_email_configured():
            tasks.append(self.send_email(
                subject=f"[{severity.upper()}] PulseWatch Alert",
                body=f"Alert ID: {alert_id}\nSeverity: {severity}\nMessage: {message}"
            ))
        else:
            logger.info("notification skipped — email not configured")
        if self._is_webhook_configured():
            tasks.append(self.send_webhook(
                payload={
                    "alert_id": alert_id,
                    "severity": severity,
                    "message": message,
                    "type": "alert_created"
                }
            ))
        else:
            logger.info("notification skipped — webhook not configured")

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def _is_email_configured(self) -> bool:
        return bool(self.smtp_server and self.smtp_to_email and self.smtp_from_email)

    def _is_webhook_configured(self) -> bool:
        return bool(self.webhook_url)

    async def send_email(self, subject: str, body: str):
        """Send an email notification."""
        if not self._is_email_configured():
            return
            
        def _send():
            try:
                msg = MIMEMultipart()
                msg['From'] = self.smtp_from_email
                msg['To'] = self.smtp_to_email
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'plain'))

                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server: # type: ignore
                    server.starttls()
                    if self.smtp_username and self.smtp_password:
                        server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)
                logger.info(f"Email notification sent to {self.smtp_to_email}")
            except Exception as e:
                logger.error(f"Failed to send email notification: {e}")

        await asyncio.to_thread(_send)

    async def send_webhook(self, payload: dict):
        """Send a generic webhook POST notification."""
        if not self._is_webhook_configured():
            return

        def _send():
            try:
                response = requests.post(
                    self.webhook_url, # type: ignore
                    json=payload,
                    timeout=5
                )
                response.raise_for_status()
                logger.info(f"Webhook notification sent to {self.webhook_url}")
            except Exception as e:
                logger.error(f"Failed to send webhook notification: {e}")

        await asyncio.to_thread(_send)
