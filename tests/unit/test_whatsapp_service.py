"""Unit tests for the WhatsApp notification service.

Tests cover:
- Service is disabled by default (no Twilio calls made)
- send_message returns True when disabled
- send_message succeeds when enabled and Twilio returns a message SID
- send_message returns False when Twilio raises an exception
- Phone number normalisation (whatsapp: prefix added when missing)
"""

from unittest.mock import MagicMock, patch

import pytest
from src.notifications.whatsapp_service import WhatsAppMessage, WhatsAppService


def _settings(enabled: bool = False) -> MagicMock:
    """Build a minimal mock Settings object."""
    s = MagicMock()
    s.whatsapp_enabled = enabled
    s.twilio_account_sid = "AC123"
    s.twilio_auth_token = "token456"
    s.twilio_whatsapp_from = "whatsapp:+14155238886"
    return s


class TestWhatsAppServiceDisabled:
    def test_is_enabled_false_by_default(self) -> None:
        service = WhatsAppService(_settings(enabled=False))
        assert service.is_enabled is False

    @pytest.mark.asyncio
    async def test_send_returns_true_when_disabled(self) -> None:
        service = WhatsAppService(_settings(enabled=False))
        msg = WhatsAppMessage(to="+595981234567", body="Hello")
        result = await service.send_message(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_no_twilio_call_when_disabled(self) -> None:
        with patch("src.notifications.whatsapp_service.TwilioClient") as mock_client_cls:
            service = WhatsAppService(_settings(enabled=False))
            msg = WhatsAppMessage(to="+595981234567", body="Hello")
            await service.send_message(msg)
            mock_client_cls.assert_not_called()


class TestWhatsAppServiceEnabled:
    def _enabled_service(self) -> WhatsAppService:
        with patch("src.notifications.whatsapp_service.TwilioClient") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            service = WhatsAppService(_settings(enabled=True))
            # Store the mock for later assertions
            service._mock_client = mock_client  # type: ignore[attr-defined]
            return service

    @pytest.mark.asyncio
    async def test_send_returns_true_on_success(self) -> None:
        with patch("src.notifications.whatsapp_service.TwilioClient") as mock_cls:
            mock_client = MagicMock()
            mock_message = MagicMock()
            mock_message.sid = "SM123"
            mock_client.messages.create.return_value = mock_message
            mock_cls.return_value = mock_client

            service = WhatsAppService(_settings(enabled=True))
            msg = WhatsAppMessage(to="+595981234567", body="Test message")
            result = await service.send_message(msg)

        assert result is True

    @pytest.mark.asyncio
    async def test_send_calls_twilio_with_correct_params(self) -> None:
        with patch("src.notifications.whatsapp_service.TwilioClient") as mock_cls:
            mock_client = MagicMock()
            mock_message = MagicMock()
            mock_message.sid = "SM123"
            mock_client.messages.create.return_value = mock_message
            mock_cls.return_value = mock_client

            service = WhatsAppService(_settings(enabled=True))
            msg = WhatsAppMessage(to="+595981234567", body="Test")
            await service.send_message(msg)

            mock_client.messages.create.assert_called_once_with(
                from_="whatsapp:+14155238886",
                to="whatsapp:+595981234567",
                body="Test",
            )

    @pytest.mark.asyncio
    async def test_send_returns_false_on_exception(self) -> None:
        with patch("src.notifications.whatsapp_service.TwilioClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("Network error")
            mock_cls.return_value = mock_client

            service = WhatsAppService(_settings(enabled=True))
            msg = WhatsAppMessage(to="+595981234567", body="Test")
            result = await service.send_message(msg)

        assert result is False

    @pytest.mark.asyncio
    async def test_number_without_prefix_gets_normalised(self) -> None:
        with patch("src.notifications.whatsapp_service.TwilioClient") as mock_cls:
            mock_client = MagicMock()
            mock_message = MagicMock()
            mock_message.sid = "SM999"
            mock_client.messages.create.return_value = mock_message
            mock_cls.return_value = mock_client

            service = WhatsAppService(_settings(enabled=True))
            await service.send_message(WhatsAppMessage(to="+595981234567", body="Hi"))

            call_kwargs = mock_client.messages.create.call_args
            assert call_kwargs.kwargs["to"] == "whatsapp:+595981234567"

    @pytest.mark.asyncio
    async def test_number_with_prefix_not_doubled(self) -> None:
        with patch("src.notifications.whatsapp_service.TwilioClient") as mock_cls:
            mock_client = MagicMock()
            mock_message = MagicMock()
            mock_message.sid = "SM888"
            mock_client.messages.create.return_value = mock_message
            mock_cls.return_value = mock_client

            service = WhatsAppService(_settings(enabled=True))
            await service.send_message(
                WhatsAppMessage(to="whatsapp:+595981234567", body="Already prefixed")
            )

            call_kwargs = mock_client.messages.create.call_args
            # Must not become "whatsapp:whatsapp:+..."
            assert call_kwargs.kwargs["to"] == "whatsapp:+595981234567"


class TestWhatsAppMessageNormalisation:
    def test_normalise_adds_prefix(self) -> None:
        result = WhatsAppService._normalise_number("+595981234567")
        assert result == "whatsapp:+595981234567"

    def test_normalise_preserves_existing_prefix(self) -> None:
        result = WhatsAppService._normalise_number("whatsapp:+595981234567")
        assert result == "whatsapp:+595981234567"
