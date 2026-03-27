"""WhatsApp notification service using the Twilio REST API.

Send-only integration for pre-approved WhatsApp Business message templates.
Wraps the Twilio Python SDK and provides a transport-agnostic interface so
callers do not depend on Twilio internals.

Usage::

    service = WhatsAppService(settings)
    success = await service.send_message(
        to="+595981234567",
        body="Your adoption application has been approved!",
    )
"""

import logging
from dataclasses import dataclass

from src.config import Settings

logger = logging.getLogger(__name__)

# Twilio is an optional runtime dependency. If the library is not installed
# the service will raise ImportError only when actually enabled and used.
try:
    from twilio.rest import Client as TwilioClient
except ImportError:
    TwilioClient = None  # type: ignore[assignment,misc]


@dataclass(frozen=True)
class WhatsAppMessage:
    """Value object representing an outbound WhatsApp message."""

    to: str
    body: str


class WhatsAppService:
    """Send WhatsApp messages via the Twilio API.

    The service reads Twilio configuration from Settings at construction time.
    When whatsapp_enabled is False, send_message() logs the attempt and returns
    True without contacting Twilio — safe for tests and local development.

    Phone numbers supplied to send_message() must be in E.164 format
    (e.g. "+595981234567"). The service prepends the "whatsapp:" URI scheme
    required by Twilio automatically.
    """

    def __init__(self, settings: Settings) -> None:
        self._enabled = settings.whatsapp_enabled
        self._account_sid = settings.twilio_account_sid
        self._auth_token = settings.twilio_auth_token
        self._from_number = settings.twilio_whatsapp_from
        self._client: object | None = None

        if self._enabled:
            if TwilioClient is None:
                raise ImportError(
                    "twilio package is required when whatsapp_enabled=True. "
                    "Install it with: pip install twilio"
                )
            self._client = TwilioClient(self._account_sid, self._auth_token)

    @property
    def is_enabled(self) -> bool:
        """Whether WhatsApp delivery is configured and enabled."""
        return self._enabled

    async def send_message(self, message: WhatsAppMessage) -> bool:
        """Send a WhatsApp message to a single recipient.

        Returns True when the message was accepted by Twilio (or when the
        service is disabled). Returns False on delivery error.

        Note: Twilio's Python SDK is synchronous. We call it directly here
        because WhatsApp volume is low and the blocking call is short. For
        high-volume deployments, wrap this in asyncio.run_in_executor().
        """
        if not self._enabled:
            logger.info(
                "WhatsApp delivery disabled — would send to=%s body=%r",
                message.to,
                message.body[:50],
            )
            return True

        to_address = self._normalise_number(message.to)

        try:
            client: TwilioClient = self._client  # type: ignore[assignment]
            result = client.messages.create(
                from_=self._from_number,
                to=to_address,
                body=message.body,
            )
            logger.info(
                "WhatsApp message queued: sid=%s to=%s",
                result.sid,
                message.to,
            )
            return True
        except Exception as exc:
            logger.error(
                "WhatsApp delivery failed: to=%s error=%s",
                message.to,
                str(exc),
            )
            return False

    @staticmethod
    def _normalise_number(phone: str) -> str:
        """Ensure the phone number has the 'whatsapp:' URI scheme Twilio requires."""
        if phone.startswith("whatsapp:"):
            return phone
        return f"whatsapp:{phone}"
