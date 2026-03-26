"""Unit tests for sponsorship service logic.

Tests sponsorship lifecycle with mocked database and Stripe API.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.db.models.sponsorship import SponsorshipStatus
from src.services.sponsorship_service import (
    cancel_sponsorship,
    create_sponsorship,
    get_animal_sponsors,
    get_donor_sponsorships,
    handle_subscription_updated,
    update_sponsorship,
)


class TestCreateSponsorship:
    """Tests for create_sponsorship function."""

    @pytest.mark.asyncio
    async def test_creates_sponsorship_without_stripe(self) -> None:
        donor = MagicMock()
        donor.id = uuid4()

        db = AsyncMock()
        db.get.return_value = donor

        # No existing sponsorship
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        result = await create_sponsorship(
            db=db,
            donor_id=donor.id,
            animal_id=uuid4(),
            tier="bronze",
        )

        assert result is not None
        assert result.tier == "bronze"
        assert result.amount_cents == 1000
        assert result.status == SponsorshipStatus.ACTIVE.value
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_when_donor_not_found(self) -> None:
        db = AsyncMock()
        db.get.return_value = None

        with pytest.raises(ValueError, match="not found"):
            await create_sponsorship(
                db=db,
                donor_id=uuid4(),
                animal_id=uuid4(),
                tier="silver",
            )

    @pytest.mark.asyncio
    async def test_raises_when_duplicate_active_sponsorship(self) -> None:
        donor = MagicMock()
        donor.id = uuid4()

        existing = MagicMock()
        existing.status = SponsorshipStatus.ACTIVE.value

        db = AsyncMock()
        db.get.return_value = donor

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="already has an active"):
            await create_sponsorship(
                db=db,
                donor_id=donor.id,
                animal_id=uuid4(),
                tier="gold",
            )

    @pytest.mark.asyncio
    async def test_gold_tier_sets_correct_amount(self) -> None:
        donor = MagicMock()
        donor.id = uuid4()

        db = AsyncMock()
        db.get.return_value = donor

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        result = await create_sponsorship(
            db=db,
            donor_id=donor.id,
            animal_id=uuid4(),
            tier="gold",
        )

        assert result.amount_cents == 5000

    @pytest.mark.asyncio
    async def test_silver_tier_sets_correct_amount(self) -> None:
        donor = MagicMock()
        donor.id = uuid4()

        db = AsyncMock()
        db.get.return_value = donor

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        result = await create_sponsorship(
            db=db,
            donor_id=donor.id,
            animal_id=uuid4(),
            tier="silver",
        )

        assert result.amount_cents == 2500


class TestUpdateSponsorship:
    """Tests for update_sponsorship function."""

    @pytest.mark.asyncio
    async def test_pause_active_sponsorship(self) -> None:
        sponsorship = MagicMock()
        sponsorship.status = SponsorshipStatus.ACTIVE.value
        sponsorship.stripe_subscription_id = None

        db = AsyncMock()
        db.get.return_value = sponsorship

        result = await update_sponsorship(
            db=db,
            sponsorship_id=uuid4(),
            action="pause",
        )

        assert result is not None
        assert result.status == SponsorshipStatus.PAUSED.value
        assert result.paused_at is not None
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_resume_paused_sponsorship(self) -> None:
        sponsorship = MagicMock()
        sponsorship.status = SponsorshipStatus.PAUSED.value
        sponsorship.stripe_subscription_id = None

        db = AsyncMock()
        db.get.return_value = sponsorship

        result = await update_sponsorship(
            db=db,
            sponsorship_id=uuid4(),
            action="resume",
        )

        assert result is not None
        assert result.status == SponsorshipStatus.ACTIVE.value
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_change_tier(self) -> None:
        sponsorship = MagicMock()
        sponsorship.status = SponsorshipStatus.ACTIVE.value
        sponsorship.tier = "bronze"
        sponsorship.stripe_subscription_id = None

        db = AsyncMock()
        db.get.return_value = sponsorship

        result = await update_sponsorship(
            db=db,
            sponsorship_id=uuid4(),
            tier="gold",
        )

        assert result is not None
        assert result.tier == "gold"
        assert result.amount_cents == 5000
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self) -> None:
        db = AsyncMock()
        db.get.return_value = None

        result = await update_sponsorship(
            db=db,
            sponsorship_id=uuid4(),
            action="pause",
        )

        assert result is None


class TestCancelSponsorship:
    """Tests for cancel_sponsorship function."""

    @pytest.mark.asyncio
    async def test_cancels_active_sponsorship(self) -> None:
        sponsorship = MagicMock()
        sponsorship.status = SponsorshipStatus.ACTIVE.value
        sponsorship.stripe_subscription_id = None

        db = AsyncMock()
        db.get.return_value = sponsorship

        result = await cancel_sponsorship(db=db, sponsorship_id=uuid4())

        assert result is not None
        assert result.status == SponsorshipStatus.CANCELLED.value
        assert result.cancelled_at is not None
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_idempotent_when_already_cancelled(self) -> None:
        sponsorship = MagicMock()
        sponsorship.status = SponsorshipStatus.CANCELLED.value

        db = AsyncMock()
        db.get.return_value = sponsorship

        result = await cancel_sponsorship(db=db, sponsorship_id=uuid4())

        assert result is sponsorship
        db.flush.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self) -> None:
        db = AsyncMock()
        db.get.return_value = None

        result = await cancel_sponsorship(db=db, sponsorship_id=uuid4())

        assert result is None


class TestGetDonorSponsorships:
    """Tests for get_donor_sponsorships function."""

    @pytest.mark.asyncio
    async def test_returns_list_of_sponsorships(self) -> None:
        s1 = MagicMock()
        s2 = MagicMock()

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [s1, s2]
        db.execute.return_value = mock_result

        result = await get_donor_sponsorships(db, uuid4())

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_none(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result

        result = await get_donor_sponsorships(db, uuid4())

        assert result == []


class TestGetAnimalSponsors:
    """Tests for get_animal_sponsors function."""

    @pytest.mark.asyncio
    async def test_returns_active_sponsors(self) -> None:
        s1 = MagicMock()

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [s1]
        db.execute.return_value = mock_result

        result = await get_animal_sponsors(db, uuid4())

        assert len(result) == 1


class TestHandleSubscriptionUpdated:
    """Tests for handle_subscription_updated webhook handler."""

    @pytest.mark.asyncio
    async def test_updates_status_from_webhook(self) -> None:
        sponsorship = MagicMock()
        sponsorship.id = uuid4()
        sponsorship.status = SponsorshipStatus.ACTIVE.value

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sponsorship
        db.execute.return_value = mock_result

        result = await handle_subscription_updated(db, "sub_test123", "canceled")

        assert result is not None
        assert result.status == SponsorshipStatus.CANCELLED.value
        assert result.cancelled_at is not None
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_updates_period_end(self) -> None:
        sponsorship = MagicMock()
        sponsorship.id = uuid4()
        sponsorship.status = SponsorshipStatus.ACTIVE.value

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sponsorship
        db.execute.return_value = mock_result

        result = await handle_subscription_updated(
            db, "sub_test123", "active", current_period_end=1700000000
        )

        assert result is not None
        assert result.current_period_end is not None
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        result = await handle_subscription_updated(db, "sub_nonexistent", "active")

        assert result is None

    @pytest.mark.asyncio
    async def test_maps_past_due_status(self) -> None:
        sponsorship = MagicMock()
        sponsorship.id = uuid4()
        sponsorship.status = SponsorshipStatus.ACTIVE.value

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sponsorship
        db.execute.return_value = mock_result

        result = await handle_subscription_updated(db, "sub_test123", "past_due")

        assert result is not None
        assert result.status == SponsorshipStatus.PAST_DUE.value
