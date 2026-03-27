"""Unit tests for stripe_error_handler and payment error constants.

Covers:
  - stripe_error_handler: CardError -> 402
  - stripe_error_handler: CardError with known decline codes -> specific messages
  - stripe_error_handler: AuthenticationError -> 503
  - stripe_error_handler: RateLimitError -> 503 with Retry-After
  - stripe_error_handler: InvalidRequestError -> 400
  - stripe_error_handler: APIConnectionError -> 503
  - stripe_error_handler: generic StripeError -> 502
  - Payment error code constants are uppercase and unique
"""

import json
from unittest.mock import MagicMock

import pytest
import stripe
from src.middleware.error_handler import (
    _CARD_DECLINE_MESSAGES,
    _CARD_DECLINED_GENERIC,
    stripe_error_handler,
)
from src.schemas.error import (
    ERROR_CARD_DECLINED,
    ERROR_INSUFFICIENT_BALANCE,
    ERROR_INVALID_PAYMENT_PARAMS,
    ERROR_PAYMENT_SERVICE_UNAVAILABLE,
    ERROR_RATE_LIMITED,
    ERROR_WEBHOOK_VERIFICATION_FAILED,
)


def _make_request(request_id: str | None = None) -> MagicMock:
    """Create a mock Request with optional request_id in state."""
    request = MagicMock()
    if request_id:
        request.state.request_id = request_id
    else:
        del request.state.request_id
    return request


class TestStripeCardError:
    """Tests for CardError -> 402 CARD_DECLINED."""

    @pytest.mark.asyncio
    async def test_card_error_returns_402(self) -> None:
        request = _make_request("req-pay-001")
        exc = stripe.CardError("card declined", "card", "card_declined")

        response = await stripe_error_handler(request, exc)

        assert response.status_code == 402
        body = json.loads(response.body)
        assert body["error_code"] == ERROR_CARD_DECLINED
        assert body["request_id"] == "req-pay-001"

    @pytest.mark.asyncio
    async def test_card_error_insufficient_funds_message(self) -> None:
        request = _make_request("req-pay-002")
        exc = stripe.CardError("insufficient funds", "card", "insufficient_funds")

        response = await stripe_error_handler(request, exc)

        body = json.loads(response.body)
        assert "insufficient" in body["message"].lower()

    @pytest.mark.asyncio
    async def test_card_error_expired_card_message(self) -> None:
        request = _make_request("req-pay-003")
        exc = stripe.CardError("expired", "card", "expired_card")

        response = await stripe_error_handler(request, exc)

        body = json.loads(response.body)
        assert "expired" in body["message"].lower()

    @pytest.mark.asyncio
    async def test_card_error_unknown_decline_code_uses_generic(self) -> None:
        request = _make_request("req-pay-004")
        exc = stripe.CardError("some unknown reason", "card", "some_unknown_code")

        response = await stripe_error_handler(request, exc)

        body = json.loads(response.body)
        assert body["message"] == _CARD_DECLINED_GENERIC

    @pytest.mark.asyncio
    async def test_card_error_no_decline_code_uses_generic(self) -> None:
        request = _make_request("req-pay-005")
        # code=None simulates missing decline code
        exc = stripe.CardError("declined", "card", None)

        response = await stripe_error_handler(request, exc)

        body = json.loads(response.body)
        assert body["message"] == _CARD_DECLINED_GENERIC


class TestStripeAuthenticationError:
    """Tests for AuthenticationError -> 503 PAYMENT_SERVICE_UNAVAILABLE."""

    @pytest.mark.asyncio
    async def test_auth_error_returns_503(self) -> None:
        request = _make_request("req-pay-010")
        exc = stripe.AuthenticationError("invalid api key")

        response = await stripe_error_handler(request, exc)

        assert response.status_code == 503
        body = json.loads(response.body)
        assert body["error_code"] == ERROR_PAYMENT_SERVICE_UNAVAILABLE

    @pytest.mark.asyncio
    async def test_auth_error_does_not_expose_key(self) -> None:
        request = _make_request("req-pay-011")
        exc = stripe.AuthenticationError("No API key provided")

        response = await stripe_error_handler(request, exc)

        body = json.loads(response.body)
        assert "api" not in body["message"].lower()
        assert "key" not in body["message"].lower()


class TestStripeRateLimitError:
    """Tests for RateLimitError -> 503 with Retry-After header."""

    @pytest.mark.asyncio
    async def test_rate_limit_returns_503(self) -> None:
        request = _make_request("req-pay-020")
        exc = stripe.RateLimitError("too many requests")

        response = await stripe_error_handler(request, exc)

        assert response.status_code == 503
        body = json.loads(response.body)
        assert body["error_code"] == ERROR_RATE_LIMITED

    @pytest.mark.asyncio
    async def test_rate_limit_includes_retry_after_header(self) -> None:
        request = _make_request("req-pay-021")
        exc = stripe.RateLimitError("too many requests")

        response = await stripe_error_handler(request, exc)

        assert "Retry-After" in response.headers
        assert int(response.headers["Retry-After"]) > 0


class TestStripeInvalidRequestError:
    """Tests for InvalidRequestError -> 400 INVALID_PAYMENT_PARAMS."""

    @pytest.mark.asyncio
    async def test_invalid_request_returns_400(self) -> None:
        request = _make_request("req-pay-030")
        exc = stripe.InvalidRequestError("invalid amount", "amount")

        response = await stripe_error_handler(request, exc)

        assert response.status_code == 400
        body = json.loads(response.body)
        assert body["error_code"] == ERROR_INVALID_PAYMENT_PARAMS

    @pytest.mark.asyncio
    async def test_invalid_request_does_not_leak_stripe_details(self) -> None:
        request = _make_request("req-pay-031")
        # Simulate Stripe returning internal/sensitive error detail
        exc = stripe.InvalidRequestError(
            "amount must be greater than 0 (internal_id: abc123)", "amount"
        )

        response = await stripe_error_handler(request, exc)

        body = json.loads(response.body)
        # Should NOT echo the stripe message back
        assert "internal_id" not in body["message"]


class TestStripeAPIConnectionError:
    """Tests for APIConnectionError -> 503 PAYMENT_SERVICE_UNAVAILABLE."""

    @pytest.mark.asyncio
    async def test_connection_error_returns_503(self) -> None:
        request = _make_request("req-pay-040")
        exc = stripe.APIConnectionError("network error")

        response = await stripe_error_handler(request, exc)

        assert response.status_code == 503
        body = json.loads(response.body)
        assert body["error_code"] == ERROR_PAYMENT_SERVICE_UNAVAILABLE


class TestStripeGenericError:
    """Tests for base StripeError fallback -> 502."""

    @pytest.mark.asyncio
    async def test_generic_stripe_error_returns_502(self) -> None:
        request = _make_request("req-pay-050")
        exc = stripe.StripeError("something unexpected")

        response = await stripe_error_handler(request, exc)

        assert response.status_code == 502
        body = json.loads(response.body)
        assert body["error_code"] == ERROR_PAYMENT_SERVICE_UNAVAILABLE

    @pytest.mark.asyncio
    async def test_generic_stripe_error_includes_request_id(self) -> None:
        request = _make_request("req-pay-051")
        exc = stripe.StripeError("error")

        response = await stripe_error_handler(request, exc)

        body = json.loads(response.body)
        assert body["request_id"] == "req-pay-051"


class TestPaymentErrorConstants:
    """Tests for payment error code constants."""

    def test_payment_constants_are_uppercase(self) -> None:
        codes = [
            ERROR_CARD_DECLINED,
            ERROR_PAYMENT_SERVICE_UNAVAILABLE,
            ERROR_INVALID_PAYMENT_PARAMS,
            ERROR_WEBHOOK_VERIFICATION_FAILED,
            ERROR_INSUFFICIENT_BALANCE,
        ]
        for code in codes:
            assert isinstance(code, str)
            assert code == code.upper(), f"Code {code!r} is not uppercase"

    def test_payment_constants_are_unique(self) -> None:
        codes = [
            ERROR_CARD_DECLINED,
            ERROR_PAYMENT_SERVICE_UNAVAILABLE,
            ERROR_INVALID_PAYMENT_PARAMS,
            ERROR_WEBHOOK_VERIFICATION_FAILED,
            ERROR_INSUFFICIENT_BALANCE,
        ]
        assert len(set(codes)) == len(codes)

    def test_decline_messages_registry_is_populated(self) -> None:
        assert len(_CARD_DECLINE_MESSAGES) > 0
        for code, message in _CARD_DECLINE_MESSAGES.items():
            assert isinstance(code, str) and len(code) > 0
            assert isinstance(message, str) and len(message) > 10

    def test_all_known_decline_codes_have_specific_messages(self) -> None:
        """Known decline codes must not use the generic fallback message."""
        for code, message in _CARD_DECLINE_MESSAGES.items():
            assert (
                message != _CARD_DECLINED_GENERIC
            ), f"Decline code '{code}' uses generic fallback message"
