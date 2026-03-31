"""Unit tests for the Meta Cloud WhatsApp service.

Tests cover:
- Service disabled by default (no HTTP calls made)
- send_text returns True when disabled
- send_template returns True when disabled
- send_text succeeds and calls correct endpoint with correct payload
- send_template succeeds with template payload
- API errors (4xx/5xx) return False
- Network errors return False
- Phone number normalisation (leading '+' stripped)
- messages URL built correctly from config
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from src.notifications.meta_whatsapp_service import (
    DEFAULT_MESSAGING_PRODUCT,
    MetaTemplateMessage,
    MetaTextMessage,
    MetaWhatsAppService,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _settings(enabled: bool = False) -> MagicMock:
    """Build a minimal mock Settings object for MetaWhatsAppService."""
    s = MagicMock()
    s.meta_whatsapp_enabled = enabled
    s.meta_whatsapp_token = "test-bearer-token"
    s.meta_whatsapp_phone_number_id = "123456789"
    s.meta_whatsapp_api_version = "v18.0"
    s.meta_whatsapp_api_base_url = "https://graph.facebook.com"
    return s


def _mock_client(status_code: int = 200, json_body: dict | None = None) -> AsyncMock:
    """Return an AsyncMock httpx.AsyncClient that returns a canned response."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_body or {"messages": [{"id": "wamid.test123"}]}
    if status_code >= 400:
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=MagicMock(),
            response=mock_response,
        )
        mock_response.text = f'{{"error": {{"code": {status_code}}}}}'
    else:
        mock_response.raise_for_status.return_value = None

    client = AsyncMock(spec=httpx.AsyncClient)
    client.post.return_value = mock_response
    client.aclose = AsyncMock()
    return client


# ---------------------------------------------------------------------------
# Disabled state tests
# ---------------------------------------------------------------------------


class TestMetaWhatsAppServiceDisabled:
    def test_is_enabled_false_by_default(self) -> None:
        service = MetaWhatsAppService(_settings(enabled=False))
        assert service.is_enabled is False

    @pytest.mark.asyncio
    async def test_send_text_returns_true_when_disabled(self) -> None:
        service = MetaWhatsAppService(_settings(enabled=False))
        result = await service.send_text(MetaTextMessage(to="+595981234567", body="Hola"))
        assert result is True

    @pytest.mark.asyncio
    async def test_send_template_returns_true_when_disabled(self) -> None:
        service = MetaWhatsAppService(_settings(enabled=False))
        result = await service.send_template(
            MetaTemplateMessage(
                to="+595981234567",
                template_name="adoption_approved",
                language_code="es",
            )
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_no_http_call_when_disabled(self) -> None:
        client = _mock_client()
        service = MetaWhatsAppService(_settings(enabled=False), http_client=client)
        await service.send_text(MetaTextMessage(to="+595981234567", body="Hola"))
        client.post.assert_not_called()


# ---------------------------------------------------------------------------
# send_text tests
# ---------------------------------------------------------------------------


class TestMetaWhatsAppServiceSendText:
    @pytest.mark.asyncio
    async def test_send_text_returns_true_on_success(self) -> None:
        client = _mock_client(200)
        service = MetaWhatsAppService(_settings(enabled=True), http_client=client)
        result = await service.send_text(MetaTextMessage(to="+595981234567", body="Hola mundo"))
        assert result is True

    @pytest.mark.asyncio
    async def test_send_text_calls_correct_url(self) -> None:
        client = _mock_client(200)
        service = MetaWhatsAppService(_settings(enabled=True), http_client=client)
        await service.send_text(MetaTextMessage(to="+595981234567", body="Test"))

        call_args = client.post.call_args
        url = call_args.args[0] if call_args.args else call_args.kwargs.get("url", "")
        assert "v18.0" in url
        assert "123456789" in url
        assert "messages" in url

    @pytest.mark.asyncio
    async def test_send_text_payload_structure(self) -> None:
        client = _mock_client(200)
        service = MetaWhatsAppService(_settings(enabled=True), http_client=client)
        await service.send_text(MetaTextMessage(to="+595981234567", body="Test body"))

        call_kwargs = client.post.call_args.kwargs
        payload = call_kwargs["json"]
        assert payload["messaging_product"] == DEFAULT_MESSAGING_PRODUCT
        assert payload["to"] == "595981234567"  # '+' stripped
        assert payload["type"] == "text"
        assert payload["text"]["body"] == "Test body"

    @pytest.mark.asyncio
    async def test_send_text_includes_bearer_token(self) -> None:
        client = _mock_client(200)
        service = MetaWhatsAppService(_settings(enabled=True), http_client=client)
        await service.send_text(MetaTextMessage(to="+595981234567", body="Token test"))

        call_kwargs = client.post.call_args.kwargs
        assert call_kwargs["headers"]["Authorization"] == "Bearer test-bearer-token"

    @pytest.mark.asyncio
    async def test_send_text_returns_false_on_http_error(self) -> None:
        client = _mock_client(400)
        service = MetaWhatsAppService(_settings(enabled=True), http_client=client)
        result = await service.send_text(MetaTextMessage(to="+595981234567", body="Fail"))
        assert result is False

    @pytest.mark.asyncio
    async def test_send_text_returns_false_on_server_error(self) -> None:
        client = _mock_client(500)
        service = MetaWhatsAppService(_settings(enabled=True), http_client=client)
        result = await service.send_text(MetaTextMessage(to="+595981234567", body="Fail"))
        assert result is False

    @pytest.mark.asyncio
    async def test_send_text_returns_false_on_network_error(self) -> None:
        client = AsyncMock(spec=httpx.AsyncClient)
        client.post.side_effect = httpx.RequestError("Connection refused", request=MagicMock())
        client.aclose = AsyncMock()
        service = MetaWhatsAppService(_settings(enabled=True), http_client=client)
        result = await service.send_text(MetaTextMessage(to="+595981234567", body="Network fail"))
        assert result is False


# ---------------------------------------------------------------------------
# send_template tests
# ---------------------------------------------------------------------------


class TestMetaWhatsAppServiceSendTemplate:
    @pytest.mark.asyncio
    async def test_send_template_returns_true_on_success(self) -> None:
        client = _mock_client(200)
        service = MetaWhatsAppService(_settings(enabled=True), http_client=client)
        result = await service.send_template(
            MetaTemplateMessage(
                to="+595981234567",
                template_name="adoption_approved",
                language_code="es",
                components=[
                    {
                        "type": "body",
                        "parameters": [{"type": "text", "text": "Luna"}],
                    }
                ],
            )
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_send_template_payload_structure(self) -> None:
        client = _mock_client(200)
        service = MetaWhatsAppService(_settings(enabled=True), http_client=client)
        await service.send_template(
            MetaTemplateMessage(
                to="+595981234567",
                template_name="donation_receipt",
                language_code="es",
                components=[],
            )
        )

        call_kwargs = client.post.call_args.kwargs
        payload = call_kwargs["json"]
        assert payload["type"] == "template"
        assert payload["template"]["name"] == "donation_receipt"
        assert payload["template"]["language"]["code"] == "es"
        assert payload["to"] == "595981234567"

    @pytest.mark.asyncio
    async def test_send_template_returns_false_on_error(self) -> None:
        client = _mock_client(401)
        service = MetaWhatsAppService(_settings(enabled=True), http_client=client)
        result = await service.send_template(
            MetaTemplateMessage(
                to="+595981234567",
                template_name="test_template",
                language_code="es",
            )
        )
        assert result is False


# ---------------------------------------------------------------------------
# Phone normalisation tests
# ---------------------------------------------------------------------------


class TestPhoneNormalisation:
    def test_strips_leading_plus(self) -> None:
        assert MetaWhatsAppService._normalise_number("+595981234567") == "595981234567"

    def test_no_plus_unchanged(self) -> None:
        assert MetaWhatsAppService._normalise_number("595981234567") == "595981234567"

    def test_number_without_country_code_unchanged(self) -> None:
        assert MetaWhatsAppService._normalise_number("981234567") == "981234567"

    @pytest.mark.asyncio
    async def test_send_text_normalises_phone_in_payload(self) -> None:
        client = _mock_client(200)
        service = MetaWhatsAppService(_settings(enabled=True), http_client=client)
        await service.send_text(MetaTextMessage(to="+595981234567", body="Hi"))
        payload = client.post.call_args.kwargs["json"]
        assert payload["to"] == "595981234567"


# ---------------------------------------------------------------------------
# URL construction tests
# ---------------------------------------------------------------------------


class TestMessagesUrl:
    def test_url_contains_api_version(self) -> None:
        service = MetaWhatsAppService(_settings())
        url = service._messages_url()
        assert "v18.0" in url

    def test_url_contains_phone_number_id(self) -> None:
        service = MetaWhatsAppService(_settings())
        url = service._messages_url()
        assert "123456789" in url

    def test_url_ends_with_messages(self) -> None:
        service = MetaWhatsAppService(_settings())
        url = service._messages_url()
        assert url.endswith("/messages")

    def test_url_uses_base_url(self) -> None:
        service = MetaWhatsAppService(_settings())
        url = service._messages_url()
        assert url.startswith("https://graph.facebook.com")

    def test_url_trailing_slash_in_base_stripped(self) -> None:
        s = _settings()
        s.meta_whatsapp_api_base_url = "https://graph.facebook.com/"
        service = MetaWhatsAppService(s)
        url = service._messages_url()
        assert "facebook.com//" not in url
