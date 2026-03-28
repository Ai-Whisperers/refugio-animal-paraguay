"""Unit tests for rescuer campaign service.

Tests cover: auto-approval logic, campaign dict serialization,
status transitions, and error raises.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from src.services.rescuer_campaign_service import (
    RescuerCampaignNotFoundError,
    RescuerCampaignPermissionError,
    RescuerNotFoundError,
    _campaign_to_dict,
    create_rescuer_campaign,
    end_rescuer_campaign,
    get_rescuer_campaign,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def make_rescuer(is_verified: bool = True) -> MagicMock:
    """Build a mock RescuerProfile."""
    r = MagicMock()
    r.id = uuid4()
    r.is_verified = is_verified
    r.display_name = "Maria Test"
    r.slug = "maria-test"
    return r


def make_campaign(rescuer_id=None, status: str = "active") -> MagicMock:
    """Build a mock Campaign."""
    c = MagicMock()
    c.id = uuid4()
    c.rescuer_id = rescuer_id or uuid4()
    c.title = "Ayuda para Luna"
    c.description = "Luna necesita tratamiento veterinario urgente."
    c.target_amount_cents = 50000  # €500
    c.currency = "EUR"
    c.fund_category = "medical"
    c.status = status
    c.goal_message = "Juntos podemos ayudar a Luna"
    c.animal_ids = []
    c.photo_urls = []
    c.deadline = None
    c.requires_approval = False
    c.created_at = datetime.now(UTC)
    c.updated_at = datetime.now(UTC)
    return c


# ---------------------------------------------------------------------------
# _campaign_to_dict
# ---------------------------------------------------------------------------


class TestCampaignToDict:
    """Tests for the _campaign_to_dict helper serializer."""

    def test_converts_cents_to_eur(self) -> None:
        campaign = make_campaign()
        campaign.target_amount_cents = 75000
        result = _campaign_to_dict(campaign, raised_cents=25000, donor_count=3)
        assert result["target_amount_eur"] == 750.0
        assert result["raised_amount_eur"] == 250.0

    def test_donor_count_included(self) -> None:
        campaign = make_campaign()
        result = _campaign_to_dict(campaign, raised_cents=0, donor_count=7)
        assert result["donor_count"] == 7

    def test_all_required_keys_present(self) -> None:
        campaign = make_campaign()
        result = _campaign_to_dict(campaign, raised_cents=0, donor_count=0)
        required = {
            "id",
            "title",
            "description",
            "target_amount_eur",
            "raised_amount_eur",
            "donor_count",
            "fund_category",
            "status",
            "goal_message",
            "animal_ids",
            "photo_urls",
            "deadline",
            "requires_approval",
            "created_at",
            "updated_at",
        }
        assert required.issubset(set(result.keys()))

    def test_empty_animal_ids_returns_list(self) -> None:
        campaign = make_campaign()
        campaign.animal_ids = None
        result = _campaign_to_dict(campaign, raised_cents=0, donor_count=0)
        assert result["animal_ids"] == []

    def test_empty_photo_urls_returns_list(self) -> None:
        campaign = make_campaign()
        campaign.photo_urls = None
        result = _campaign_to_dict(campaign, raised_cents=0, donor_count=0)
        assert result["photo_urls"] == []


# ---------------------------------------------------------------------------
# create_rescuer_campaign
# ---------------------------------------------------------------------------


class TestCreateRescuerCampaign:
    """Tests for campaign creation with auto-approval logic."""

    @pytest.mark.asyncio
    async def test_verified_rescuer_creates_active_campaign(self) -> None:
        rescuer = make_rescuer(is_verified=True)
        db = AsyncMock()

        created_campaign = make_campaign(rescuer_id=rescuer.id, status="active")

        with (
            patch(
                "src.services.rescuer_campaign_service._get_rescuer_by_user",
                new=AsyncMock(return_value=rescuer),
            ),
            patch(
                "src.services.rescuer_campaign_service.Campaign",
                return_value=created_campaign,
            ),
        ):
            db.add = MagicMock()
            db.flush = AsyncMock()
            db.refresh = AsyncMock()

            result = await create_rescuer_campaign(
                user_id=uuid4(),
                title="Ayuda urgente para Max",
                description="Max necesita cirugía de emergencia por una fractura.",
                target_amount_eur=300.0,
                fund_category="medical",
                goal_message=None,
                animal_ids=[],
                photo_urls=[],
                deadline=None,
                db=db,
            )

        assert result["status"] == "active"
        assert result["requires_approval"] is False

    @pytest.mark.asyncio
    async def test_unverified_rescuer_creates_draft_with_approval(self) -> None:
        rescuer = make_rescuer(is_verified=False)
        db = AsyncMock()

        created_campaign = make_campaign(rescuer_id=rescuer.id, status="draft")
        created_campaign.requires_approval = True

        with (
            patch(
                "src.services.rescuer_campaign_service._get_rescuer_by_user",
                new=AsyncMock(return_value=rescuer),
            ),
            patch(
                "src.services.rescuer_campaign_service.Campaign",
                return_value=created_campaign,
            ),
        ):
            db.add = MagicMock()
            db.flush = AsyncMock()
            db.refresh = AsyncMock()

            result = await create_rescuer_campaign(
                user_id=uuid4(),
                title="Campana de rescatista no verificado",
                description="Una campana creada por un rescatista pendiente de verificacion.",
                target_amount_eur=100.0,
                fund_category="rescue",
                goal_message=None,
                animal_ids=[],
                photo_urls=[],
                deadline=None,
                db=db,
            )

        assert result["status"] == "draft"
        assert result["requires_approval"] is True

    @pytest.mark.asyncio
    async def test_raises_rescuer_not_found_if_no_profile(self) -> None:
        db = AsyncMock()

        with (
            patch(
                "src.services.rescuer_campaign_service._get_rescuer_by_user",
                new=AsyncMock(side_effect=RescuerNotFoundError("no profile")),
            ),
            pytest.raises(RescuerNotFoundError),
        ):
            await create_rescuer_campaign(
                user_id=uuid4(),
                title="Test",
                description="Description with enough characters to pass validation.",
                target_amount_eur=100.0,
                fund_category="general",
                goal_message=None,
                animal_ids=[],
                photo_urls=[],
                deadline=None,
                db=db,
            )

    @pytest.mark.asyncio
    async def test_target_amount_converted_to_cents(self) -> None:
        rescuer = make_rescuer(is_verified=True)
        db = AsyncMock()

        captured_campaign = None

        def capture_campaign(**kwargs):
            nonlocal captured_campaign
            c = make_campaign(rescuer_id=rescuer.id)
            c.target_amount_cents = kwargs.get("target_amount_cents", 0)
            captured_campaign = c
            return c

        with (
            patch(
                "src.services.rescuer_campaign_service._get_rescuer_by_user",
                new=AsyncMock(return_value=rescuer),
            ),
            patch(
                "src.services.rescuer_campaign_service.Campaign",
                side_effect=capture_campaign,
            ),
        ):
            db.add = MagicMock()
            db.flush = AsyncMock()
            db.refresh = AsyncMock()

            await create_rescuer_campaign(
                user_id=uuid4(),
                title="Price conversion test",
                description="Testing that EUR to cents conversion works correctly.",
                target_amount_eur=123.45,
                fund_category="general",
                goal_message=None,
                animal_ids=[],
                photo_urls=[],
                deadline=None,
                db=db,
            )

        assert captured_campaign is not None
        assert captured_campaign.target_amount_cents == 12345


# ---------------------------------------------------------------------------
# end_rescuer_campaign
# ---------------------------------------------------------------------------


class TestEndRescuerCampaign:
    """Tests for completing or archiving a campaign."""

    @pytest.mark.asyncio
    async def test_complete_action_sets_completed_status(self) -> None:
        rescuer = make_rescuer()
        campaign = make_campaign(rescuer_id=rescuer.id, status="active")
        db = AsyncMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()

        select_result = MagicMock()
        select_result.scalar_one_or_none.return_value = campaign
        db.execute = AsyncMock(return_value=select_result)

        with (
            patch(
                "src.services.rescuer_campaign_service._get_rescuer_by_user",
                new=AsyncMock(return_value=rescuer),
            ),
            patch(
                "src.services.rescuer_campaign_service._aggregate_campaign_donations",
                new=AsyncMock(return_value=(0, 0)),
            ),
        ):
            result = await end_rescuer_campaign(
                user_id=uuid4(),
                campaign_id=campaign.id,
                action="complete",
                impact_message="Gracias a todos por su apoyo!",
                db=db,
            )

        assert campaign.status == "completed"
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_archive_action_sets_archived_status(self) -> None:
        rescuer = make_rescuer()
        campaign = make_campaign(rescuer_id=rescuer.id, status="active")
        db = AsyncMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()

        select_result = MagicMock()
        select_result.scalar_one_or_none.return_value = campaign
        db.execute = AsyncMock(return_value=select_result)

        with (
            patch(
                "src.services.rescuer_campaign_service._get_rescuer_by_user",
                new=AsyncMock(return_value=rescuer),
            ),
            patch(
                "src.services.rescuer_campaign_service._aggregate_campaign_donations",
                new=AsyncMock(return_value=(0, 0)),
            ),
        ):
            await end_rescuer_campaign(
                user_id=uuid4(),
                campaign_id=campaign.id,
                action="archive",
                impact_message=None,
                db=db,
            )

        assert campaign.status == "archived"

    @pytest.mark.asyncio
    async def test_raises_not_found_when_campaign_missing(self) -> None:
        rescuer = make_rescuer()
        db = AsyncMock()

        select_result = MagicMock()
        select_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=select_result)

        with (
            patch(
                "src.services.rescuer_campaign_service._get_rescuer_by_user",
                new=AsyncMock(return_value=rescuer),
            ),
            pytest.raises(RescuerCampaignNotFoundError),
        ):
            await end_rescuer_campaign(
                user_id=uuid4(),
                campaign_id=uuid4(),
                action="complete",
                impact_message=None,
                db=db,
            )

    @pytest.mark.asyncio
    async def test_raises_permission_error_when_not_owner(self) -> None:
        rescuer = make_rescuer()
        other_rescuer_id = uuid4()
        campaign = make_campaign(rescuer_id=other_rescuer_id, status="active")
        db = AsyncMock()

        select_result = MagicMock()
        select_result.scalar_one_or_none.return_value = campaign
        db.execute = AsyncMock(return_value=select_result)

        with (
            patch(
                "src.services.rescuer_campaign_service._get_rescuer_by_user",
                new=AsyncMock(return_value=rescuer),
            ),
            pytest.raises(RescuerCampaignPermissionError),
        ):
            await end_rescuer_campaign(
                user_id=uuid4(),
                campaign_id=campaign.id,
                action="complete",
                impact_message=None,
                db=db,
            )


# ---------------------------------------------------------------------------
# get_rescuer_campaign
# ---------------------------------------------------------------------------


class TestGetRescuerCampaign:
    """Tests for fetching a single rescuer campaign."""

    @pytest.mark.asyncio
    async def test_returns_campaign_dict(self) -> None:
        rescuer = make_rescuer()
        campaign = make_campaign(rescuer_id=rescuer.id)
        db = AsyncMock()

        select_result = MagicMock()
        select_result.scalar_one_or_none.return_value = campaign
        db.execute = AsyncMock(return_value=select_result)

        with (
            patch(
                "src.services.rescuer_campaign_service._get_rescuer_by_user",
                new=AsyncMock(return_value=rescuer),
            ),
            patch(
                "src.services.rescuer_campaign_service._aggregate_campaign_donations",
                new=AsyncMock(return_value=(10000, 2)),
            ),
        ):
            result = await get_rescuer_campaign(user_id=uuid4(), campaign_id=campaign.id, db=db)

        assert result["id"] == campaign.id
        assert result["raised_amount_eur"] == 100.0
        assert result["donor_count"] == 2

    @pytest.mark.asyncio
    async def test_raises_not_found_when_campaign_missing(self) -> None:
        rescuer = make_rescuer()
        db = AsyncMock()

        select_result = MagicMock()
        select_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=select_result)

        with (
            patch(
                "src.services.rescuer_campaign_service._get_rescuer_by_user",
                new=AsyncMock(return_value=rescuer),
            ),
            pytest.raises(RescuerCampaignNotFoundError),
        ):
            await get_rescuer_campaign(user_id=uuid4(), campaign_id=uuid4(), db=db)
