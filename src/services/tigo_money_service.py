"""Tigo Money payment service for local PYG donations.

Tigo Money is Paraguay's dominant mobile wallet. This service wraps the
Tigo Money HTTP API using the standard payment gateway pattern:

  1. Initiate  — POST to Tigo API to create a payment session, get a checkout URL
  2. Redirect  — donor completes payment in Tigo app/web; Tigo calls our webhook
  3. Callback  — verify HMAC signature, mark donation complete, emit domain event

The service is disabled by default. When tigo_money_enabled=False, all methods
log the attempt and return graceful no-ops, making it safe for local dev and
environments without Tigo credentials.

References:
  Tigo Money Paraguay Business API — https://developers.tigo.com.py (sandbox available)
"""

import hashlib
import hmac
import logging
import uuid
from dataclasses import dataclass, field
from decimal import Decimal

import httpx

from src.config import Settings

logger = logging.getLogger(__name__)

# Tigo Money transaction status codes from the API
TIGO_STATUS_PENDING = "PENDING"
TIGO_STATUS_COMPLETED = "COMPLETED"
TIGO_STATUS_FAILED = "FAILED"
TIGO_STATUS_CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class TigoPaymentSession:
    """Represents a Tigo Money checkout session created by the API."""

    transaction_id: str
    checkout_url: str
    amount_pyg: int
    reference: str


@dataclass(frozen=True)
class TigoCallbackPayload:
    """Parsed and verified payload from a Tigo Money webhook callback."""

    transaction_id: str
    reference: str
    status: str
    amount_pyg: int
    raw: dict = field(default_factory=dict)


class TigoMoneyService:
    """Wrapper around the Tigo Money payment API.

    Call initiate_payment() to start a checkout session, then verify_callback()
    on the incoming webhook to confirm the payment outcome.
    """

    def __init__(self, settings: Settings) -> None:
        self._enabled = settings.tigo_money_enabled
        self._merchant_id = settings.tigo_merchant_id
        self._api_key = settings.tigo_api_key
        self._webhook_secret = settings.tigo_webhook_secret
        self._base_url = settings.tigo_api_base_url.rstrip("/")

    @property
    def is_enabled(self) -> bool:
        """Whether Tigo Money is configured and enabled."""
        return self._enabled

    async def initiate_payment(
        self,
        amount_pyg: int,
        reference: str,
        return_url: str,
        description: str = "Donación — Refugio Animal Paraguay",
    ) -> TigoPaymentSession | None:
        """Create a Tigo Money checkout session.

        Returns a TigoPaymentSession with the checkout URL to redirect the donor to,
        or None if the service is disabled or the API call fails.

        Args:
            amount_pyg: Donation amount in Paraguayan guaraníes (integer, no decimals).
            reference: Internal donation ID — used to correlate the webhook callback.
            return_url: URL Tigo redirects the donor to after payment (success or failure).
            description: Payment description displayed to the donor in Tigo app.
        """
        if not self._enabled:
            logger.info(
                "Tigo Money disabled — would initiate payment amount_pyg=%d reference=%s",
                amount_pyg,
                reference,
            )
            return None

        payload = {
            "merchantId": self._merchant_id,
            "amount": str(amount_pyg),
            "currency": "PYG",
            "reference": reference,
            "description": description,
            "returnUrl": return_url,
            "notificationUrl": f"{return_url.split('/tigo')[0]}/tigo-money/callback",
        }

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self._base_url}/payments/initiate",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

            transaction_id = data.get("transactionId") or str(uuid.uuid4())
            checkout_url = data["checkoutUrl"]

            logger.info(
                "Tigo Money session created: transaction_id=%s reference=%s amount_pyg=%d",
                transaction_id,
                reference,
                amount_pyg,
            )
            return TigoPaymentSession(
                transaction_id=transaction_id,
                checkout_url=checkout_url,
                amount_pyg=amount_pyg,
                reference=reference,
            )
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Tigo Money API error: status=%d body=%s",
                exc.response.status_code,
                exc.response.text[:200],
            )
            return None
        except Exception as exc:
            logger.error("Tigo Money initiate_payment failed: %s", str(exc))
            return None

    def verify_callback(self, payload: dict, signature: str) -> TigoCallbackPayload | None:
        """Verify a Tigo Money webhook callback and return the parsed payload.

        Tigo signs callbacks using HMAC-SHA256 over the JSON body. The signature
        is sent in the X-Tigo-Signature request header.

        Returns None when the signature is invalid or the payload is malformed.
        """
        if not self._enabled:
            return None

        if not self._webhook_secret:
            logger.warning("tigo_webhook_secret is not set — cannot verify callback signature")
            return None

        # Reconstruct the expected signature
        import json

        body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
        expected = hmac.new(
            self._webhook_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected, signature):
            logger.warning("Tigo Money callback signature mismatch — rejecting")
            return None

        try:
            return TigoCallbackPayload(
                transaction_id=payload["transactionId"],
                reference=payload["reference"],
                status=payload["status"],
                amount_pyg=int(Decimal(str(payload.get("amount", 0)))),
                raw=payload,
            )
        except (KeyError, ValueError, TypeError) as exc:
            logger.error("Tigo Money callback payload malformed: %s", str(exc))
            return None

    @staticmethod
    def pyg_to_cents(amount_pyg: int) -> int:
        """Guaraníes have no minor unit — 1 PYG = 1 cent for our DB storage."""
        return amount_pyg
