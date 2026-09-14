import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.notification_service import NotificationService

@pytest.mark.asyncio
async def test_send_alert_notification_unconfigured():
    service = NotificationService()
    service.smtp_server = None
    service.webhook_url = None
    
    # Should complete without error when neither email nor webhook is configured
    await service.send_alert_notification("alert_123", "critical", "High CPU")

@pytest.mark.asyncio
async def test_send_webhook_success():
    service = NotificationService()
    service.webhook_url = "https://example.com/webhook"
    
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        await service.send_webhook({"alert_id": "a1", "severity": "critical"})
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://example.com/webhook"
        assert kwargs["json"]["alert_id"] == "a1"

@pytest.mark.asyncio
async def test_send_email_success():
    service = NotificationService()
    service.smtp_server = "smtp.example.com"
    service.smtp_to_email = "dev@example.com"
    service.smtp_from_email = "alerts@example.com"
    
    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_smtp = MagicMock()
        mock_smtp.__enter__.return_value = mock_smtp
        mock_smtp_cls.return_value = mock_smtp
        
        await service.send_email("Critical Alert", "Details...")
        mock_smtp.starttls.assert_called_once()
        mock_smtp.send_message.assert_called_once()
