"""WhatsApp Business notification service using Meta Cloud API.

Sends WhatsApp messages directly via the Meta Graph API without Twilio.
Supports both free-form text messages (within 24-hour customer-service window)
and structured template messages (usable any time).

Meta Cloud API reference:
  https://developers.facebook.com/docs/whatsapp/cloud-api/messages

Usage::

    service = MetaWhatsAppService(settings)

    # Send a text message (only within 24h of last user message)
    success = await service.send_text(
        to="+595981234567",
        body="Tu solicitud ha sido aprobada.",
    )

    # Send a pre-approved template message
    success = await service.send_template(
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
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

from src.config import Settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MESSAGES_ENDPOINT = "/{api_version}/{phone_number_id}/messages"
DEFAULT_MESSAGING_PRODUCT = "whatsapp"
DEFAULT_RECIPIENT_TYPE = "individual"


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MetaTextMessage:
    """Value object for a free-form text WhatsApp message."""

    to: str
    body: str


@dataclass(frozen=True)
class MetaTemplateMessage:
    """Value object for a WhatsApp template message.

    `components` is the list of component objects (header, body, button)
    each with their parameter substitutions as defined in the approved template.
    """

    to: str
    template_name: str
    language_code: str
    components: list[dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class MetaWhatsAppService:
    """Send WhatsApp messages via the Meta Cloud API.

    The service reads Meta configuration from Settings at construction time.
    When meta_whatsapp_enabled is False, all send methods log the attempt and
    return True without contacting the API — safe for tests and local dev.

    Phone numbers must be in E.164 format WITHOUT the leading '+':
    Meta expects "595981234567", not "+595981234567".
    The service strips the '+' automatically.
    """

    def __init__(self, settings: Settings, http_client: httpx.AsyncClient | None = None) -> None:
        self._enabled = settings.meta_whatsapp_enabled
        self._token = settings.meta_whatsapp_token
        self._phone_number_id = settings.meta_whatsapp_phone_number_id
        self._api_version = settings.meta_whatsapp_api_version
        self._base_url = settings.meta_whatsapp_api_base_url.rstrip("/")
        self._http_client = http_client  # injected in tests; created lazily in prod

    @property
    def is_enabled(self) -> bool:
        """Whether Meta Cloud WhatsApp delivery is configured and enabled."""
        return self._enabled

    # ------------------------------------------------------------------
    # Public send methods
    # ------------------------------------------------------------------

    async def send_text(self, message: MetaTextMessage) -> bool:
        """Send a free-form text message.

        Only valid within a 24-hour customer service window (user must have
        messaged first). Use send_template for proactive outbound messages.

        Returns True on success (or when disabled). Returns False on API error.
        """
        if not self._enabled:
            logger.info(
                "Meta WhatsApp disabled — would send text to=%s body=%r",
                message.to,
                message.body[:50],
            )
            return True

        payload: dict[str, Any] = {
            "messaging_product": DEFAULT_MESSAGING_PRODUCT,
            "recipient_type": DEFAULT_RECIPIENT_TYPE,
            "to": self._normalise_number(message.to),
            "type": "text",
            "text": {"preview_url": False, "body": message.body},
        }
        return await self._post_message(payload, to=message.to)

    async def send_template(self, message: MetaTemplateMessage) -> bool:
        """Send a pre-approved template message.

        Template messages can be sent at any time (not limited to 24h window).
        The template must be registered and approved in Meta Business Manager.

        Returns True on success (or when disabled). Returns False on API error.
        """
        if not self._enabled:
            logger.info(
                "Meta WhatsApp disabled — would send template=%s to=%s",
                message.template_name,
                message.to,
            )
            return True

        payload: dict[str, Any] = {
            "messaging_product": DEFAULT_MESSAGING_PRODUCT,
            "to": self._normalise_number(message.to),
            "type": "template",
            "template": {
                "name": message.template_name,
                "language": {"code": message.language_code},
                "components": message.components,
            },
        }
        return await self._post_message(payload, to=message.to)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _post_message(self, payload: dict[str, Any], *, to: str) -> bool:
        """POST a message payload to the Meta Cloud API.

        Returns True if the API accepted the message (2xx response).
        Returns False on any HTTP or network error.
        """
        url = self._messages_url()
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }
        client = self._http_client or httpx.AsyncClient(timeout=15.0)
        owned = self._http_client is None  # True when we created the client

        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            message_id = data.get("messages", [{}])[0].get("id", "unknown")
            logger.info(
                "Meta WhatsApp message accepted: id=%s to=%s",
                message_id,
                to,
            )
            return True
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Meta WhatsApp API error: status=%s to=%s body=%s",
                exc.response.status_code,
                to,
                exc.response.text[:200],
            )
            return False
        except httpx.RequestError as exc:
            logger.error(
                "Meta WhatsApp network error: to=%s error=%s",
                to,
                str(exc),
            )
            return False
        finally:
            if owned:
                await client.aclose()

    def _messages_url(self) -> str:
        """Build the full Messages API endpoint URL."""
        path = MESSAGES_ENDPOINT.format(
            api_version=self._api_version,
            phone_number_id=self._phone_number_id,
        )
        return f"{self._base_url}{path}"

    @staticmethod
    def _normalise_number(phone: str) -> str:
        """Strip leading '+' from E.164 numbers.

        Meta Cloud API expects numbers without the '+' prefix.
        E.g. "+595981234567" → "595981234567".
        """
        return phone.lstrip("+")
