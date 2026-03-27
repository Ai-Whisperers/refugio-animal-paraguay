"""Unit tests for the Tigo Money payment service.

Tests cover:
- Service is disabled by default (no HTTP calls made)
- initiate_payment returns None when disabled
- initiate_payment returns TigoPaymentSession on success
- initiate_payment returns None on API HTTP error
- initiate_payment returns None on network exception
- verify_callback returns None when disabled
- verify_callback returns None on signature mismatch
- verify_callback returns TigoCallbackPayload on valid signature
- verify_callback returns None on malformed payload
- pyg_to_cents is identity (PYG has no minor unit)
"""

import hashlib
import hmac
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.services.tigo_money_service import (
    TIGO_STATUS_COMPLETED,
    TigoCallbackPayload,
    TigoMoneyService,
    TigoPaymentSession,
)


def _settings(enabled: bool = False, secret: str = "testsecret") -> MagicMock:
    s = MagicMock()
    s.tigo_money_enabled = enabled
    s.tigo_merchant_id = "MERCHANT_001"
    s.tigo_api_key = "apikey123"
    s.tigo_webhook_secret = secret
    s.tigo_api_base_url = "https://sandbox.tigo.com.py/v1"
    return s


class TestTigoMoneyServiceDisabled:
    def test_is_enabled_false_by_default(self) -> None:
        svc = TigoMoneyService(_settings(enabled=False))
        assert svc.is_enabled is False

    @pytest.mark.asyncio
    async def test_initiate_returns_none_when_disabled(self) -> None:
        svc = TigoMoneyService(_settings(enabled=False))
        result = await svc.initiate_payment(
            amount_pyg=100000,
            reference="ref-001",
            return_url="https://example.com/return",
        )
        assert result is None

    def test_verify_callback_returns_none_when_disabled(self) -> None:
        svc = TigoMoneyService(_settings(enabled=False))
        result = svc.verify_callback({"transactionId": "txn-001"}, "sig")
        assert result is None


class TestTigoMoneyServiceEnabled:
    @pytest.mark.asyncio
    async def test_initiate_returns_session_on_success(self) -> None:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "transactionId": "TXN-ABC123",
            "checkoutUrl": "https://pay.tigo.com.py/checkout/TXN-ABC123",
        }

        with patch("src.services.tigo_money_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            svc = TigoMoneyService(_settings(enabled=True))
            session = await svc.initiate_payment(
                amount_pyg=150000,
                reference="ref-002",
                return_url="https://example.com/return",
            )

        assert isinstance(session, TigoPaymentSession)
        assert session.transaction_id == "TXN-ABC123"
        assert "TXN-ABC123" in session.checkout_url
        assert session.amount_pyg == 150000
        assert session.reference == "ref-002"

    @pytest.mark.asyncio
    async def test_initiate_returns_none_on_http_error(self) -> None:
        import httpx

        with patch("src.services.tigo_money_service.httpx.AsyncClient") as mock_client_cls:
            mock_response = MagicMock()
            mock_response.status_code = 503
            mock_response.text = "Service unavailable"

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "503",
                    request=MagicMock(),
                    response=mock_response,
                )
            )
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            svc = TigoMoneyService(_settings(enabled=True))
            result = await svc.initiate_payment(
                amount_pyg=100000,
                reference="ref-003",
                return_url="https://example.com/return",
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_initiate_returns_none_on_network_exception(self) -> None:
        with patch("src.services.tigo_money_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=Exception("Connection refused"))
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            svc = TigoMoneyService(_settings(enabled=True))
            result = await svc.initiate_payment(
                amount_pyg=100000,
                reference="ref-004",
                return_url="https://example.com/return",
            )

        assert result is None


class TestTigoCallbackVerification:
    def _make_signature(self, payload: dict, secret: str) -> str:
        body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
        return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    def test_valid_signature_returns_payload(self) -> None:
        secret = "mysecret"
        payload = {
            "transactionId": "TXN-XYZ",
            "reference": "ref-abc",
            "status": "COMPLETED",
            "amount": "200000",
        }
        sig = self._make_signature(payload, secret)

        svc = TigoMoneyService(_settings(enabled=True, secret=secret))
        result = svc.verify_callback(payload, sig)

        assert isinstance(result, TigoCallbackPayload)
        assert result.transaction_id == "TXN-XYZ"
        assert result.status == TIGO_STATUS_COMPLETED
        assert result.amount_pyg == 200000

    def test_invalid_signature_returns_none(self) -> None:
        svc = TigoMoneyService(_settings(enabled=True, secret="secret"))
        payload = {
            "transactionId": "TXN-XYZ",
            "reference": "ref",
            "status": "COMPLETED",
            "amount": "100",
        }
        result = svc.verify_callback(payload, "wrongsignature")
        assert result is None

    def test_missing_webhook_secret_returns_none(self) -> None:
        svc = TigoMoneyService(_settings(enabled=True, secret=""))
        result = svc.verify_callback({}, "anysig")
        assert result is None

    def test_malformed_payload_returns_none(self) -> None:
        secret = "mysecret"
        payload: dict = {}
        sig = self._make_signature(payload, secret)

        svc = TigoMoneyService(_settings(enabled=True, secret=secret))
        result = svc.verify_callback(payload, sig)
        assert result is None


class TestPygToCents:
    def test_pyg_to_cents_is_identity(self) -> None:
        # PYG has no minor unit — 1 guaraní = 1 stored unit
        assert TigoMoneyService.pyg_to_cents(100000) == 100000
        assert TigoMoneyService.pyg_to_cents(1) == 1
        assert TigoMoneyService.pyg_to_cents(0) == 0
