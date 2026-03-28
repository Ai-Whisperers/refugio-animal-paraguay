"""Unit tests for the public rescuer support endpoint schemas."""

from uuid import uuid4

import pytest
from pydantic import ValidationError
from src.api.public_rescuer_support import RescuerSupportRequest, RescuerSupportResponse


class TestRescuerSupportRequest:
    """Tests for RescuerSupportRequest schema validation."""

    def test_valid_one_time_request(self) -> None:
        req = RescuerSupportRequest(
            rescuer_user_id=uuid4(),
            amount_cents=2000,
            currency="EUR",
            is_recurring=False,
            donor_name="Maria Garcia",
            donor_email="maria@example.com",
            is_anonymous=False,
        )
        assert req.amount_cents == 2000
        assert req.is_recurring is False
        assert req.is_anonymous is False

    def test_valid_recurring_request(self) -> None:
        req = RescuerSupportRequest(
            rescuer_user_id=uuid4(),
            amount_cents=5000,
            currency="EUR",
            is_recurring=True,
            donor_name="Juan Lopez",
            donor_email="juan@example.com",
        )
        assert req.is_recurring is True

    def test_valid_anonymous_request(self) -> None:
        req = RescuerSupportRequest(
            rescuer_user_id=uuid4(),
            amount_cents=1000,
            currency="EUR",
            donor_name="Ana Torres",
            donor_email="ana@example.com",
            is_anonymous=True,
        )
        assert req.is_anonymous is True

    def test_rejects_below_minimum(self) -> None:
        with pytest.raises(ValidationError, match="greater than or equal to 500"):
            RescuerSupportRequest(
                rescuer_user_id=uuid4(),
                amount_cents=100,
                currency="EUR",
                donor_name="Test",
                donor_email="test@example.com",
            )

    def test_rejects_non_eur(self) -> None:
        with pytest.raises(ValidationError, match="EUR"):
            RescuerSupportRequest(
                rescuer_user_id=uuid4(),
                amount_cents=1000,
                currency="USD",
                donor_name="Test",
                donor_email="test@example.com",
            )

    def test_rejects_empty_name(self) -> None:
        with pytest.raises(ValidationError):
            RescuerSupportRequest(
                rescuer_user_id=uuid4(),
                amount_cents=1000,
                currency="EUR",
                donor_name="",
                donor_email="test@example.com",
            )

    def test_rejects_invalid_email(self) -> None:
        with pytest.raises(ValidationError):
            RescuerSupportRequest(
                rescuer_user_id=uuid4(),
                amount_cents=1000,
                currency="EUR",
                donor_name="Test",
                donor_email="not-an-email",
            )

    def test_default_not_recurring(self) -> None:
        req = RescuerSupportRequest(
            rescuer_user_id=uuid4(),
            amount_cents=1000,
            currency="EUR",
            donor_name="Test",
            donor_email="test@example.com",
        )
        assert req.is_recurring is False

    def test_default_not_anonymous(self) -> None:
        req = RescuerSupportRequest(
            rescuer_user_id=uuid4(),
            amount_cents=1000,
            currency="EUR",
            donor_name="Test",
            donor_email="test@example.com",
        )
        assert req.is_anonymous is False

    def test_currency_uppercased(self) -> None:
        req = RescuerSupportRequest(
            rescuer_user_id=uuid4(),
            amount_cents=1000,
            currency="eur",
            donor_name="Test",
            donor_email="test@example.com",
        )
        assert req.currency == "EUR"


class TestRescuerSupportResponse:
    """Tests for RescuerSupportResponse schema."""

    def test_full_response(self) -> None:
        resp = RescuerSupportResponse(
            donation_id=str(uuid4()),
            rescuer_name="Ana Rescatista",
            donor_email="donor@example.com",
            amount_cents=5000,
            currency="EUR",
            is_recurring=True,
            stripe_checkout_url="https://checkout.stripe.com/test",
            message="Support recorded",
        )
        assert resp.amount_cents == 5000
        assert resp.is_recurring is True
        assert resp.stripe_checkout_url is not None

    def test_response_without_stripe(self) -> None:
        resp = RescuerSupportResponse(
            donation_id=str(uuid4()),
            rescuer_name="Ana",
            donor_email="donor@example.com",
            amount_cents=1000,
            currency="EUR",
            is_recurring=False,
            stripe_checkout_url=None,
            message="Support recorded",
        )
        assert resp.stripe_checkout_url is None
        assert resp.is_recurring is False

    def test_one_time_response(self) -> None:
        resp = RescuerSupportResponse(
            donation_id=str(uuid4()),
            rescuer_name="Carlos",
            donor_email="test@example.com",
            amount_cents=10000,
            currency="EUR",
            is_recurring=False,
            message="Done",
        )
        assert resp.amount_cents == 10000
