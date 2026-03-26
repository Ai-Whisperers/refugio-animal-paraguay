"""Unit tests for src/schemas/sponsorship.py and src/db/models/sponsorship.py."""

from uuid import uuid4

import pytest
from pydantic import ValidationError
from src.db.models.sponsorship import (
    BRONZE_AMOUNT_CENTS,
    GOLD_AMOUNT_CENTS,
    SILVER_AMOUNT_CENTS,
    SponsorshipFrequency,
    SponsorshipStatus,
    SponsorshipTierLevel,
)
from src.schemas.sponsorship import (
    SponsorshipCancelRequest,
    SponsorshipCreate,
    SponsorshipPauseRequest,
    SponsorshipTierUpdate,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestTierPricingConstants:
    def test_bronze_amount(self) -> None:
        assert BRONZE_AMOUNT_CENTS == 1000  # $10.00/month

    def test_silver_amount(self) -> None:
        assert SILVER_AMOUNT_CENTS == 2500  # $25.00/month

    def test_gold_amount(self) -> None:
        assert GOLD_AMOUNT_CENTS == 5000  # $50.00/month

    def test_tier_ordering(self) -> None:
        assert BRONZE_AMOUNT_CENTS < SILVER_AMOUNT_CENTS < GOLD_AMOUNT_CENTS


# ---------------------------------------------------------------------------
# SponsorshipTierLevel enum
# ---------------------------------------------------------------------------


class TestSponsorshipTierLevel:
    def test_bronze_value(self) -> None:
        assert SponsorshipTierLevel.BRONZE == "bronze"

    def test_silver_value(self) -> None:
        assert SponsorshipTierLevel.SILVER == "silver"

    def test_gold_value(self) -> None:
        assert SponsorshipTierLevel.GOLD == "gold"

    def test_all_levels_covered(self) -> None:
        levels = {lvl.value for lvl in SponsorshipTierLevel}
        assert levels == {"bronze", "silver", "gold"}


# ---------------------------------------------------------------------------
# SponsorshipStatus enum
# ---------------------------------------------------------------------------


class TestSponsorshipStatus:
    def test_active_value(self) -> None:
        assert SponsorshipStatus.ACTIVE == "active"

    def test_paused_value(self) -> None:
        assert SponsorshipStatus.PAUSED == "paused"

    def test_cancelled_value(self) -> None:
        assert SponsorshipStatus.CANCELLED == "cancelled"

    def test_completed_value(self) -> None:
        assert SponsorshipStatus.COMPLETED == "completed"

    def test_all_statuses_covered(self) -> None:
        statuses = {s.value for s in SponsorshipStatus}
        assert statuses == {"active", "paused", "cancelled", "completed"}


# ---------------------------------------------------------------------------
# SponsorshipFrequency enum
# ---------------------------------------------------------------------------


class TestSponsorshipFrequency:
    def test_monthly_value(self) -> None:
        assert SponsorshipFrequency.MONTHLY == "monthly"

    def test_annual_value(self) -> None:
        assert SponsorshipFrequency.ANNUAL == "annual"


# ---------------------------------------------------------------------------
# SponsorshipCreate schema
# ---------------------------------------------------------------------------


class TestSponsorshipCreate:
    def test_minimal_valid_payload_bronze(self) -> None:
        payload = SponsorshipCreate(
            donor_id=uuid4(),
            animal_id=uuid4(),
            tier_level=SponsorshipTierLevel.BRONZE,
        )
        assert payload.tier_level == SponsorshipTierLevel.BRONZE
        assert payload.frequency == SponsorshipFrequency.MONTHLY
        assert payload.notes is None

    def test_silver_monthly(self) -> None:
        payload = SponsorshipCreate(
            donor_id=uuid4(),
            animal_id=uuid4(),
            tier_level=SponsorshipTierLevel.SILVER,
            frequency=SponsorshipFrequency.MONTHLY,
        )
        assert payload.tier_level == SponsorshipTierLevel.SILVER

    def test_gold_annual(self) -> None:
        payload = SponsorshipCreate(
            donor_id=uuid4(),
            animal_id=uuid4(),
            tier_level=SponsorshipTierLevel.GOLD,
            frequency=SponsorshipFrequency.ANNUAL,
        )
        assert payload.frequency == SponsorshipFrequency.ANNUAL

    def test_with_notes(self) -> None:
        payload = SponsorshipCreate(
            donor_id=uuid4(),
            animal_id=uuid4(),
            tier_level=SponsorshipTierLevel.BRONZE,
            notes="This is a test note",
        )
        assert payload.notes == "This is a test note"

    def test_notes_too_long_raises(self) -> None:
        with pytest.raises(ValidationError):
            SponsorshipCreate(
                donor_id=uuid4(),
                animal_id=uuid4(),
                tier_level=SponsorshipTierLevel.BRONZE,
                notes="x" * 1001,
            )

    def test_notes_exactly_1000_chars_is_valid(self) -> None:
        payload = SponsorshipCreate(
            donor_id=uuid4(),
            animal_id=uuid4(),
            tier_level=SponsorshipTierLevel.BRONZE,
            notes="x" * 1000,
        )
        assert len(payload.notes) == 1000  # type: ignore[arg-type]

    def test_missing_donor_id_raises(self) -> None:
        with pytest.raises(ValidationError):
            SponsorshipCreate(
                animal_id=uuid4(),
                tier_level=SponsorshipTierLevel.BRONZE,
            )  # type: ignore[call-arg]

    def test_missing_animal_id_raises(self) -> None:
        with pytest.raises(ValidationError):
            SponsorshipCreate(
                donor_id=uuid4(),
                tier_level=SponsorshipTierLevel.BRONZE,
            )  # type: ignore[call-arg]

    def test_missing_tier_level_raises(self) -> None:
        with pytest.raises(ValidationError):
            SponsorshipCreate(
                donor_id=uuid4(),
                animal_id=uuid4(),
            )  # type: ignore[call-arg]

    def test_invalid_tier_level_raises(self) -> None:
        with pytest.raises(ValidationError):
            SponsorshipCreate(
                donor_id=uuid4(),
                animal_id=uuid4(),
                tier_level="platinum",  # type: ignore[arg-type]
            )

    def test_invalid_frequency_raises(self) -> None:
        with pytest.raises(ValidationError):
            SponsorshipCreate(
                donor_id=uuid4(),
                animal_id=uuid4(),
                tier_level=SponsorshipTierLevel.BRONZE,
                frequency="weekly",  # type: ignore[arg-type]
            )

    def test_invalid_uuid_raises(self) -> None:
        with pytest.raises(ValidationError):
            SponsorshipCreate(
                donor_id="not-a-uuid",  # type: ignore[arg-type]
                animal_id=uuid4(),
                tier_level=SponsorshipTierLevel.BRONZE,
            )


# ---------------------------------------------------------------------------
# SponsorshipTierUpdate schema
# ---------------------------------------------------------------------------


class TestSponsorshipTierUpdate:
    def test_all_none_is_valid(self) -> None:
        update = SponsorshipTierUpdate()
        assert update.stripe_price_id_monthly is None
        assert update.stripe_price_id_annual is None
        assert update.benefits is None
        assert update.active is None

    def test_set_stripe_price_ids(self) -> None:
        update = SponsorshipTierUpdate(
            stripe_price_id_monthly="price_monthly_123",
            stripe_price_id_annual="price_annual_456",
        )
        assert update.stripe_price_id_monthly == "price_monthly_123"
        assert update.stripe_price_id_annual == "price_annual_456"

    def test_set_benefits(self) -> None:
        benefits = {"includes_updates": True, "includes_certificate": False}
        update = SponsorshipTierUpdate(benefits=benefits)
        assert update.benefits == benefits

    def test_deactivate_tier(self) -> None:
        update = SponsorshipTierUpdate(active=False)
        assert update.active is False


# ---------------------------------------------------------------------------
# SponsorshipCancelRequest schema
# ---------------------------------------------------------------------------


class TestSponsorshipCancelRequest:
    def test_empty_payload_is_valid(self) -> None:
        req = SponsorshipCancelRequest()
        assert req.notes is None

    def test_with_notes(self) -> None:
        req = SponsorshipCancelRequest(notes="Donor requested cancellation")
        assert req.notes == "Donor requested cancellation"

    def test_notes_too_long_raises(self) -> None:
        with pytest.raises(ValidationError):
            SponsorshipCancelRequest(notes="x" * 1001)


# ---------------------------------------------------------------------------
# SponsorshipPauseRequest schema
# ---------------------------------------------------------------------------


class TestSponsorshipPauseRequest:
    def test_empty_payload_is_valid(self) -> None:
        req = SponsorshipPauseRequest()
        assert req.notes is None

    def test_with_notes(self) -> None:
        req = SponsorshipPauseRequest(notes="Donor on vacation for 2 months")
        assert req.notes == "Donor on vacation for 2 months"
