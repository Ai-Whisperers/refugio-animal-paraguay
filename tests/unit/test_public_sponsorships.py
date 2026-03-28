"""Unit tests for the public sponsorship endpoint and schemas."""

from uuid import uuid4

import pytest
from pydantic import ValidationError
from src.api.public_sponsorships import PublicSponsorshipRequest, PublicSponsorshipResponse
from src.db.models.sponsorship import (
    SponsorshipFrequency,
    SponsorshipStatus,
    SponsorshipTierLevel,
)

# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------


class TestPublicSponsorshipRequest:
    """Tests for PublicSponsorshipRequest schema validation."""

    def test_valid_request_with_tier(self) -> None:
        req = PublicSponsorshipRequest(
            animal_id=uuid4(),
            amount_cents=2500,
            currency="EUR",
            frequency=SponsorshipFrequency.MONTHLY,
            donor_name="Maria Garcia",
            donor_email="maria@example.com",
            tier_level=SponsorshipTierLevel.SILVER,
        )
        assert req.amount_cents == 2500
        assert req.tier_level == SponsorshipTierLevel.SILVER
        assert req.currency == "EUR"

    def test_valid_request_custom_amount(self) -> None:
        req = PublicSponsorshipRequest(
            animal_id=uuid4(),
            amount_cents=7500,
            currency="EUR",
            donor_name="Juan Lopez",
            donor_email="juan@example.com",
            tier_level=None,
        )
        assert req.amount_cents == 7500
        assert req.tier_level is None

    def test_rejects_below_minimum_amount(self) -> None:
        with pytest.raises(ValidationError, match="greater than or equal to 500"):
            PublicSponsorshipRequest(
                animal_id=uuid4(),
                amount_cents=100,
                currency="EUR",
                donor_name="Test",
                donor_email="test@example.com",
            )

    def test_rejects_non_eur_currency(self) -> None:
        with pytest.raises(ValidationError, match="EUR"):
            PublicSponsorshipRequest(
                animal_id=uuid4(),
                amount_cents=1000,
                currency="USD",
                donor_name="Test",
                donor_email="test@example.com",
            )

    def test_rejects_empty_donor_name(self) -> None:
        with pytest.raises(ValidationError):
            PublicSponsorshipRequest(
                animal_id=uuid4(),
                amount_cents=1000,
                currency="EUR",
                donor_name="",
                donor_email="test@example.com",
            )

    def test_rejects_invalid_email(self) -> None:
        with pytest.raises(ValidationError):
            PublicSponsorshipRequest(
                animal_id=uuid4(),
                amount_cents=1000,
                currency="EUR",
                donor_name="Test User",
                donor_email="not-an-email",
            )

    def test_default_frequency_is_monthly(self) -> None:
        req = PublicSponsorshipRequest(
            animal_id=uuid4(),
            amount_cents=1000,
            currency="EUR",
            donor_name="Test",
            donor_email="test@example.com",
        )
        assert req.frequency == SponsorshipFrequency.MONTHLY

    def test_accepts_annual_frequency(self) -> None:
        req = PublicSponsorshipRequest(
            animal_id=uuid4(),
            amount_cents=1000,
            currency="EUR",
            frequency=SponsorshipFrequency.ANNUAL,
            donor_name="Test",
            donor_email="test@example.com",
        )
        assert req.frequency == SponsorshipFrequency.ANNUAL

    def test_currency_uppercased(self) -> None:
        req = PublicSponsorshipRequest(
            animal_id=uuid4(),
            amount_cents=1000,
            currency="eur",
            donor_name="Test",
            donor_email="test@example.com",
        )
        assert req.currency == "EUR"


class TestPublicSponsorshipResponse:
    """Tests for PublicSponsorshipResponse schema."""

    def test_response_all_fields(self) -> None:
        resp = PublicSponsorshipResponse(
            sponsorship_id=str(uuid4()),
            animal_id=str(uuid4()),
            donor_email="donor@example.com",
            amount_cents=2500,
            currency="EUR",
            frequency="monthly",
            stripe_checkout_url="https://checkout.stripe.com/test",
            message="Sponsorship created",
        )
        assert resp.amount_cents == 2500
        assert resp.stripe_checkout_url is not None

    def test_response_without_stripe(self) -> None:
        resp = PublicSponsorshipResponse(
            sponsorship_id=str(uuid4()),
            animal_id=str(uuid4()),
            donor_email="donor@example.com",
            amount_cents=1000,
            currency="EUR",
            frequency="monthly",
            stripe_checkout_url=None,
            message="Sponsorship created",
        )
        assert resp.stripe_checkout_url is None


# ---------------------------------------------------------------------------
# Tier and model tests
# ---------------------------------------------------------------------------


class TestSponsorshipModels:
    """Tests for sponsorship-related enums and constants."""

    def test_tier_levels(self) -> None:
        assert SponsorshipTierLevel.BRONZE == "bronze"
        assert SponsorshipTierLevel.SILVER == "silver"
        assert SponsorshipTierLevel.GOLD == "gold"

    def test_frequency_values(self) -> None:
        assert SponsorshipFrequency.MONTHLY == "monthly"
        assert SponsorshipFrequency.ANNUAL == "annual"

    def test_status_values(self) -> None:
        assert SponsorshipStatus.ACTIVE == "active"
        assert SponsorshipStatus.PAUSED == "paused"
        assert SponsorshipStatus.CANCELLED == "cancelled"
        assert SponsorshipStatus.COMPLETED == "completed"

    def test_tier_level_count(self) -> None:
        assert len(SponsorshipTierLevel) == 3

    def test_status_count(self) -> None:
        assert len(SponsorshipStatus) == 4
