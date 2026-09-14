import pytest
from unittest.mock import patch, MagicMock
from app.services.notification_service import NotificationService

@pytest.mark.asyncio
async def test_notification_channels():
    service = NotificationService()
    service.smtp_server = "smtp.test.com"
    service.smtp_from_email = "from@test.com"
    service.smtp_to_email = "to@test.com"
    service.webhook_url = "https://webhook.test.com"
    
    with patch.object(service, "send_email") as mock_email, patch.object(service, "send_webhook") as mock_webhook:
        await service.send_alert_notification("alert_1", "warning", "Test message")
        mock_email.assert_called_once()
        mock_webhook.assert_called_once()
