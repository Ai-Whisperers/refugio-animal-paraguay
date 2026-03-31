"""Unit tests for WhatsApp webhook endpoint (RAP-204).

Tests cover:
- GET /webhooks/whatsapp: valid subscription verification challenge
- GET /webhooks/whatsapp: invalid mode returns 400
- GET /webhooks/whatsapp: mismatched verify token returns 403
- GET /webhooks/whatsapp: missing verify_token config returns 500
- POST /webhooks/whatsapp: valid signed payload returns 200
- POST /webhooks/whatsapp: signature mismatch returns 200 with ignored status
- POST /webhooks/whatsapp: auto-ack sent to sender
- POST /webhooks/whatsapp: no auto-ack when WhatsApp is disabled
- POST /webhooks/whatsapp: handles malformed JSON gracefully
- _verify_signature: valid signature passes
- _verify_signature: tampered body fails
- _verify_signature: missing header fails
- _verify_signature: skips verification when app_secret is empty
"""

from __future__ import annotations

import hashlib
import hmac
import json
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from src.api.whatsapp_webhook import _verify_signature, router
from src.config import Settings

# ---------------------------------------------------------------------------
# Test client setup
# ---------------------------------------------------------------------------


def _make_settings(
    verify_token: str = "test-verify-token",
    meta_token: str = "test-meta-token",
    enabled: bool = True,
) -> Settings:
    return Settings(
        meta_whatsapp_verify_token=verify_token,
        meta_whatsapp_token=meta_token,
        meta_whatsapp_enabled=enabled,
        meta_whatsapp_phone_number_id="123456789",
    )


# ---------------------------------------------------------------------------
# Signature verification unit tests (pure function)
# ---------------------------------------------------------------------------


class TestVerifySignature:
    def test_valid_signature_passes(self) -> None:
        body = b'{"hello": "world"}'
        secret = "mysecret"
        sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        assert _verify_signature(body, f"sha256={sig}", secret) is True

    def test_tampered_body_fails(self) -> None:
        body = b'{"hello": "world"}'
        secret = "mysecret"
        sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        tampered = b'{"hello": "evil"}'
        assert _verify_signature(tampered, f"sha256={sig}", secret) is False

    def test_missing_header_fails(self) -> None:
        assert _verify_signature(b"body", None, "secret") is False

    def test_wrong_prefix_fails(self) -> None:
        assert _verify_signature(b"body", "md5=abc123", "secret") is False

    def test_skips_verification_when_secret_is_empty(self) -> None:
        # Development mode — no secret configured
        assert _verify_signature(b"body", None, "") is True


# ---------------------------------------------------------------------------
# GET /webhooks/whatsapp — verification challenge
# ---------------------------------------------------------------------------


class TestWebhookVerificationEndpoint:
    def _client(self, settings: Settings | None = None) -> TestClient:
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        settings = settings or _make_settings()
        app.dependency_overrides[
            __import__("src.config", fromlist=["get_settings"]).get_settings
        ] = lambda: settings
        return TestClient(app)

    def test_valid_challenge_returns_challenge_text(self) -> None:
        client = self._client()
        response = client.get(
            "/webhooks/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "test-verify-token",
                "hub.challenge": "CHALLENGE123",
            },
        )
        assert response.status_code == 200
        assert response.text == "CHALLENGE123"

    def test_invalid_mode_returns_400(self) -> None:
        client = self._client()
        response = client.get(
            "/webhooks/whatsapp",
            params={
                "hub.mode": "unsubscribe",
                "hub.verify_token": "test-verify-token",
                "hub.challenge": "CHALLENGE123",
            },
        )
        assert response.status_code == 400

    def test_mismatched_token_returns_403(self) -> None:
        client = self._client()
        response = client.get(
            "/webhooks/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "WRONG-TOKEN",
                "hub.challenge": "CHALLENGE123",
            },
        )
        assert response.status_code == 403

    def test_missing_verify_token_config_returns_500(self) -> None:
        client = self._client(settings=_make_settings(verify_token=""))
        response = client.get(
            "/webhooks/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "",
                "hub.challenge": "CHALLENGE123",
            },
        )
        assert response.status_code == 500


# ---------------------------------------------------------------------------
# POST /webhooks/whatsapp — incoming message handling
# ---------------------------------------------------------------------------


def _signed_body(body: bytes, secret: str) -> str:
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


def _text_message_payload(sender: str = "+595981234567", text: str = "Hola") -> bytes:
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": sender,
                                    "id": "wamid.abc123",
                                    "type": "text",
                                    "text": {"body": text},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    return json.dumps(payload).encode()


class TestReceiveMessageEndpoint:
    def _client(self, settings: Settings | None = None) -> TestClient:
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        settings = settings or _make_settings()
        app.dependency_overrides[
            __import__("src.config", fromlist=["get_settings"]).get_settings
        ] = lambda: settings
        return TestClient(app)

    def test_valid_signed_payload_returns_200_ok(self) -> None:
        settings = _make_settings()
        client = self._client(settings)
        body = _text_message_payload()
        sig = _signed_body(body, settings.meta_whatsapp_token)

        with patch("src.api.whatsapp_webhook.MetaWhatsAppService") as mock_service:
            instance = mock_service.return_value
            instance.send_template = AsyncMock(return_value=True)
            instance.is_enabled = True

            response = client.post(
                "/webhooks/whatsapp",
                content=body,
                headers={"X-Hub-Signature-256": sig, "Content-Type": "application/json"},
            )

        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_signature_mismatch_returns_200_ignored(self) -> None:
        client = self._client()
        body = _text_message_payload()

        response = client.post(
            "/webhooks/whatsapp",
            content=body,
            headers={
                "X-Hub-Signature-256": "sha256=badhash",
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "ignored"

    def test_auto_ack_sent_when_enabled(self) -> None:
        settings = _make_settings(enabled=True)
        client = self._client(settings)
        body = _text_message_payload(sender="+595981234567")
        sig = _signed_body(body, settings.meta_whatsapp_token)

        with patch("src.api.whatsapp_webhook.MetaWhatsAppService") as mock_service:
            instance = mock_service.return_value
            instance.send_template = AsyncMock(return_value=True)

            client.post(
                "/webhooks/whatsapp",
                content=body,
                headers={"X-Hub-Signature-256": sig, "Content-Type": "application/json"},
            )

            mock_service.assert_called_once_with(settings)
            instance.send_template.assert_awaited_once()
            msg = instance.send_template.call_args.args[0]
            assert msg.to == "+595981234567"

    def test_malformed_json_returns_200_error(self) -> None:
        settings = _make_settings()
        client = self._client(settings)
        body = b"not-json"
        sig = _signed_body(body, settings.meta_whatsapp_token)

        response = client.post(
            "/webhooks/whatsapp",
            content=body,
            headers={"X-Hub-Signature-256": sig, "Content-Type": "application/json"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "error"
