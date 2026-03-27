"""Unit tests for SEPA and subscription Pydantic schemas."""

from uuid import uuid4

import pytest
from pydantic import ValidationError
from src.db.models.donation import CurrencyCode, RecurringInterval
from src.schemas.donation import (
    SepaIntentCreate,
    SepaIntentResponse,
    SubscriptionCancelResponse,
    SubscriptionCreate,
    SubscriptionResponse,
)


class TestSepaIntentCreate:
    """Tests for SepaIntentCreate schema."""

    def test_valid_sepa_intent(self) -> None:
        donor_id = uuid4()
        intent = SepaIntentCreate(donor_id=donor_id, amount_cents=5000)
        assert intent.donor_id == donor_id
        assert intent.amount_cents == 5000
        assert intent.notes is None

    def test_sepa_intent_with_notes(self) -> None:
        intent = SepaIntentCreate(donor_id=uuid4(), amount_cents=1000, notes="Monthly SEPA")
        assert intent.notes == "Monthly SEPA"

    def test_rejects_zero_amount(self) -> None:
        with pytest.raises(ValidationError):
            SepaIntentCreate(donor_id=uuid4(), amount_cents=0)

    def test_rejects_negative_amount(self) -> None:
        with pytest.raises(ValidationError):
            SepaIntentCreate(donor_id=uuid4(), amount_cents=-100)


class TestSepaIntentResponse:
    """Tests for SepaIntentResponse schema."""

    def test_valid_response(self) -> None:
        donation_id = uuid4()
        resp = SepaIntentResponse(
            donation_id=donation_id,
            stripe_payment_intent_id="pi_test123",
            client_secret="pi_test123_secret",
            amount_cents=5000,
        )
        assert resp.currency == CurrencyCode.EUR
        assert resp.donation_id == donation_id

    def test_default_currency_is_eur(self) -> None:
        resp = SepaIntentResponse(
            donation_id=uuid4(),
            stripe_payment_intent_id="pi_test",
            client_secret="secret",
            amount_cents=1000,
        )
        assert resp.currency == CurrencyCode.EUR


class TestSubscriptionCreate:
    """Tests for SubscriptionCreate schema."""

    def test_valid_monthly_subscription(self) -> None:
        donor_id = uuid4()
        sub = SubscriptionCreate(
            donor_id=donor_id,
            amount_cents=2000,
            payment_method_id="pm_test123",
        )
        assert sub.donor_id == donor_id
        assert sub.interval == RecurringInterval.MONTH
        assert sub.currency == CurrencyCode.EUR

    def test_valid_yearly_subscription(self) -> None:
        sub = SubscriptionCreate(
            donor_id=uuid4(),
            amount_cents=24000,
            interval=RecurringInterval.YEAR,
            payment_method_id="pm_test456",
        )
        assert sub.interval == RecurringInterval.YEAR

    def test_rejects_zero_amount(self) -> None:
        with pytest.raises(ValidationError):
            SubscriptionCreate(
                donor_id=uuid4(),
                amount_cents=0,
                payment_method_id="pm_test",
            )

    def test_requires_payment_method_id(self) -> None:
        with pytest.raises(ValidationError):
            SubscriptionCreate(
                donor_id=uuid4(),
                amount_cents=2000,
            )  # type: ignore[call-arg]

    def test_with_notes(self) -> None:
        sub = SubscriptionCreate(
            donor_id=uuid4(),
            amount_cents=1000,
            payment_method_id="pm_test",
            notes="Recurring SEPA donation",
        )
        assert sub.notes == "Recurring SEPA donation"


class TestSubscriptionResponse:
    """Tests for SubscriptionResponse schema."""

    def test_valid_response(self) -> None:
        resp = SubscriptionResponse(
            donation_id=uuid4(),
            stripe_subscription_id="sub_test123",
            stripe_customer_id="cus_test456",
            amount_cents=2000,
            currency=CurrencyCode.EUR,
            interval=RecurringInterval.MONTH,
            status="active",
        )
        assert resp.stripe_subscription_id == "sub_test123"
        assert resp.status == "active"


class TestSubscriptionCancelResponse:
    """Tests for SubscriptionCancelResponse schema."""

    def test_valid_cancel_response(self) -> None:
        resp = SubscriptionCancelResponse(
            stripe_subscription_id="sub_test123",
            status="canceled",
        )
        assert resp.stripe_subscription_id == "sub_test123"
        assert resp.status == "canceled"
