"""Unit tests for campaign service logic.

Tests campaign CRUD and progress calculation with mocked database.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.db.models.campaign import CampaignStatus
from src.services.campaign_service import (
    create_campaign,
    delete_campaign,
    get_campaign,
    get_campaign_progress,
    list_campaigns,
    update_campaign,
)


class TestCreateCampaign:
    """Tests for create_campaign function."""

    @pytest.mark.asyncio
    async def test_creates_campaign_in_draft_status(self) -> None:
        db = AsyncMock()

        result = await create_campaign(
            db=db,
            title="Medical Emergency Fund",
            goal_amount_cents=100000,
            currency="USD",
            category="medical",
        )

        assert result is not None
        assert result.title == "Medical Emergency Fund"
        assert result.goal_amount_cents == 100000
        assert result.status == CampaignStatus.DRAFT.value
        assert result.currency == "USD"
        assert result.category == "medical"
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_creates_campaign_with_description(self) -> None:
        db = AsyncMock()

        result = await create_campaign(
            db=db,
            title="Food Drive",
            goal_amount_cents=50000,
            description="Monthly food supply campaign",
        )

        assert result.description == "Monthly food supply campaign"

    @pytest.mark.asyncio
    async def test_creates_featured_campaign(self) -> None:
        db = AsyncMock()

        result = await create_campaign(
            db=db,
            title="Rescue Mission",
            goal_amount_cents=200000,
            featured=True,
        )

        assert result.featured is True

    @pytest.mark.asyncio
    async def test_creates_campaign_with_user_id(self) -> None:
        db = AsyncMock()
        user_id = uuid4()

        result = await create_campaign(
            db=db,
            title="Facility Upgrade",
            goal_amount_cents=500000,
            created_by_user_id=user_id,
        )

        assert result.created_by_user_id == user_id


class TestUpdateCampaign:
    """Tests for update_campaign function."""

    @pytest.mark.asyncio
    async def test_updates_title(self) -> None:
        campaign = MagicMock()
        campaign.title = "Old Title"

        db = AsyncMock()
        db.get.return_value = campaign

        result = await update_campaign(
            db=db,
            campaign_id=uuid4(),
            title="New Title",
        )

        assert result is not None
        assert result.title == "New Title"
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_updates_status(self) -> None:
        campaign = MagicMock()
        campaign.status = CampaignStatus.DRAFT.value

        db = AsyncMock()
        db.get.return_value = campaign

        result = await update_campaign(
            db=db,
            campaign_id=uuid4(),
            status=CampaignStatus.ACTIVE.value,
        )

        assert result is not None
        assert result.status == CampaignStatus.ACTIVE.value

    @pytest.mark.asyncio
    async def test_updates_goal_amount(self) -> None:
        campaign = MagicMock()
        campaign.goal_amount_cents = 100000

        db = AsyncMock()
        db.get.return_value = campaign

        result = await update_campaign(
            db=db,
            campaign_id=uuid4(),
            goal_amount_cents=200000,
        )

        assert result is not None
        assert result.goal_amount_cents == 200000

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self) -> None:
        db = AsyncMock()
        db.get.return_value = None

        result = await update_campaign(
            db=db,
            campaign_id=uuid4(),
            title="Anything",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_updates_featured_flag(self) -> None:
        campaign = MagicMock()
        campaign.featured = False

        db = AsyncMock()
        db.get.return_value = campaign

        result = await update_campaign(
            db=db,
            campaign_id=uuid4(),
            featured=True,
        )

        assert result is not None
        assert result.featured is True


class TestGetCampaign:
    """Tests for get_campaign function."""

    @pytest.mark.asyncio
    async def test_returns_campaign(self) -> None:
        campaign = MagicMock()

        db = AsyncMock()
        db.get.return_value = campaign

        result = await get_campaign(db, uuid4())

        assert result is campaign

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self) -> None:
        db = AsyncMock()
        db.get.return_value = None

        result = await get_campaign(db, uuid4())

        assert result is None


class TestListCampaigns:
    """Tests for list_campaigns function."""

    @pytest.mark.asyncio
    async def test_returns_list(self) -> None:
        c1 = MagicMock()
        c2 = MagicMock()

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [c1, c2]
        db.execute.return_value = mock_result

        result = await list_campaigns(db)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_returns_empty_list(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result

        result = await list_campaigns(db)

        assert result == []


class TestGetCampaignProgress:
    """Tests for get_campaign_progress function."""

    @pytest.mark.asyncio
    async def test_returns_progress_data(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.raised = 50000
        mock_row.donors = 5
        mock_result.one.return_value = mock_row
        db.execute.return_value = mock_result

        result = await get_campaign_progress(db, uuid4())

        assert result["raised_amount_cents"] == 50000
        assert result["donor_count"] == 5

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_donations(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.raised = 0
        mock_row.donors = 0
        mock_result.one.return_value = mock_row
        db.execute.return_value = mock_result

        result = await get_campaign_progress(db, uuid4())

        assert result["raised_amount_cents"] == 0
        assert result["donor_count"] == 0


class TestDeleteCampaign:
    """Tests for delete_campaign function."""

    @pytest.mark.asyncio
    async def test_deletes_draft_campaign(self) -> None:
        campaign = MagicMock()
        campaign.status = CampaignStatus.DRAFT.value

        db = AsyncMock()
        db.get.return_value = campaign

        result = await delete_campaign(db, uuid4())

        assert result is True
        db.delete.assert_awaited_once_with(campaign)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_does_not_delete_active_campaign(self) -> None:
        campaign = MagicMock()
        campaign.status = CampaignStatus.ACTIVE.value

        db = AsyncMock()
        db.get.return_value = campaign

        result = await delete_campaign(db, uuid4())

        assert result is False
        db.delete.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_false_when_not_found(self) -> None:
        db = AsyncMock()
        db.get.return_value = None

        result = await delete_campaign(db, uuid4())

        assert result is False
