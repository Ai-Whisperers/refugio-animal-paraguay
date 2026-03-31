"""Meta WhatsApp Cloud API webhook receiver (RAP-204).

Handles two-way WhatsApp conversation flow:

1. GET /webhooks/whatsapp — Meta's subscription verification challenge
2. POST /webhooks/whatsapp — receive incoming messages from users

Incoming message handling strategy:
- Log all incoming messages for staff visibility
- Send an auto-acknowledgement template (``message_received``) to the sender
- Fail gracefully on any processing error so Meta retries are not triggered

Signature verification:
- Verifies ``X-Hub-Signature-256`` header on POST requests using the
  ``meta_whatsapp_token`` as the HMAC-SHA256 secret (Meta Cloud API v20+).

Meta documentation:
  https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/components
  https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples

Endpoints added to app.py: include_router(whatsapp_webhook_router)
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status

from src.config import Settings, get_settings
from src.notifications.meta_whatsapp_service import MetaTemplateMessage, MetaWhatsAppService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/whatsapp", tags=["webhooks"])

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AUTO_ACK_TEMPLATE_NAME = "message_received"
AUTO_ACK_TEMPLATE_LANGUAGE = "es"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", status_code=status.HTTP_200_OK)
async def verify_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
    settings: Settings = Depends(get_settings),
) -> Response:
    """Handle Meta's webhook verification challenge (subscribe handshake).

    Meta sends a GET request with ``hub.mode=subscribe``, ``hub.verify_token``,
    and ``hub.challenge`` when you register or update the webhook URL in the
    Meta Developer Console. Respond with the challenge value to confirm ownership.
    """
    expected_token = settings.meta_whatsapp_verify_token

    if hub_mode != "subscribe":
        logger.warning("WhatsApp webhook verification: unexpected hub.mode=%s", hub_mode)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid hub.mode")

    if not expected_token:
        logger.error("WhatsApp webhook: meta_whatsapp_verify_token not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook verify token not configured",
        )

    if hub_verify_token != expected_token:
        logger.warning("WhatsApp webhook: verify_token mismatch — possible spoofed request")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verify token mismatch")

    logger.info("WhatsApp webhook verified successfully")
    return Response(content=hub_challenge or "", media_type="text/plain")


@router.post("", status_code=status.HTTP_200_OK)
async def receive_message(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    """Receive and process incoming WhatsApp messages.

    Meta sends a POST with the message payload. We:
    1. Verify the HMAC-SHA256 signature.
    2. Parse the incoming message payload.
    3. Log the message for staff visibility.
    4. Send an auto-acknowledgement template to the sender.

    Always returns 200 OK — returning non-2xx causes Meta to retry delivery.
    """
    body = await request.body()

    if not _verify_signature(body, x_hub_signature_256, settings.meta_whatsapp_token):
        logger.warning("WhatsApp webhook: signature verification failed — ignoring payload")
        # Return 200 to avoid Meta retry storm on misconfigured signatures
        return {"status": "ignored"}

    try:
        payload: dict[str, Any] = await request.json()
    except Exception:
        logger.error("WhatsApp webhook: could not parse JSON body")
        return {"status": "error"}

    try:
        await _process_whatsapp_payload(payload, settings)
    except Exception as exc:
        # Never return non-2xx — log and return 200 so Meta doesn't retry
        logger.exception("WhatsApp webhook: unexpected processing error: %s", exc)

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Processing helpers
# ---------------------------------------------------------------------------


async def _process_whatsapp_payload(payload: dict[str, Any], settings: Settings) -> None:
    """Extract messages from Meta payload and handle each one."""
    entries = payload.get("entry", [])
    for entry in entries:
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages", [])
            for msg in messages:
                await _handle_incoming_message(msg, settings)


async def _handle_incoming_message(
    msg: dict[str, Any],
    settings: Settings,
) -> None:
    """Process a single incoming WhatsApp message.

    Logs the message and sends an auto-acknowledgement template.
    """
    sender_phone = msg.get("from", "")
    msg_type = msg.get("type", "unknown")
    msg_id = msg.get("id", "")

    # Extract text body if present
    text_body = ""
    if msg_type == "text":
        text_body = msg.get("text", {}).get("body", "")

    logger.info(
        "WhatsApp incoming message: from=%s type=%s msg_id=%s text=%r",
        sender_phone,
        msg_type,
        msg_id,
        text_body[:100],
    )

    # Send auto-acknowledgement so the sender knows the shelter received their message
    if sender_phone and settings.meta_whatsapp_enabled:
        meta_wa = MetaWhatsAppService(settings)
        ack_message = MetaTemplateMessage(
            to=sender_phone,
            template_name=AUTO_ACK_TEMPLATE_NAME,
            language_code=AUTO_ACK_TEMPLATE_LANGUAGE,
            components=[],
        )
        success = await meta_wa.send_template(ack_message)
        if not success:
            logger.warning(
                "WhatsApp webhook: auto-ack failed for sender=%s msg_id=%s",
                sender_phone,
                msg_id,
            )


# ---------------------------------------------------------------------------
# Signature verification
# ---------------------------------------------------------------------------


def _verify_signature(body: bytes, signature_header: str | None, app_secret: str) -> bool:
    """Verify the X-Hub-Signature-256 header.

    Meta signs the raw request body with HMAC-SHA256 using the app secret
    (``meta_whatsapp_token``). Returns True when the signature is valid or
    when signature verification is disabled (empty app_secret).

    In development (app_secret is empty string), verification is skipped.
    """
    if not app_secret:
        # Not configured — skip verification in dev/test
        return True

    if not signature_header:
        logger.warning("WhatsApp webhook: missing X-Hub-Signature-256 header")
        return False

    if not signature_header.startswith("sha256="):
        logger.warning("WhatsApp webhook: unexpected signature format: %s", signature_header[:20])
        return False

    expected_sig = hmac.new(
        app_secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()

    received_sig = signature_header[len("sha256=") :]

    if not hmac.compare_digest(expected_sig, received_sig):
        logger.warning("WhatsApp webhook: HMAC mismatch — possible replay or spoofed request")
        return False

    return True
