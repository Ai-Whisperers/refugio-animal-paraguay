"""Unit tests for email campaign service — scheduling and send logic.

Tests:
- schedule_campaign state transitions and validation
- cancel_campaign state transitions and validation
- initiate_send recipient counting and status update
- get_pending_scheduled_campaigns query logic
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.db.models.email_campaign import EmailCampaign, EmailCampaignStatus
from src.services.email_campaign_service import (
    cancel_campaign,
    get_pending_scheduled_campaigns,
    initiate_send,
    schedule_campaign,
)

CAMPAIGN_ID = uuid4()
LIST_ID = uuid4()
TEMPLATE_ID = uuid4()
NOW = datetime.now(tz=UTC)


def _make_campaign(**overrides) -> MagicMock:
    defaults = {
        "id": CAMPAIGN_ID,
        "name": "Test Campaign",
        "email_list_id": LIST_ID,
        "email_template_id": TEMPLATE_ID,
        "status": EmailCampaignStatus.DRAFT,
        "scheduled_at": None,
        "sent_at": None,
        "sent_count": 0,
        "failed_count": 0,
        "total_recipients": 0,
        "created_at": NOW,
        "updated_at": NOW,
        "error_message": None,
    }
    defaults.update(overrides)
    campaign = MagicMock(spec=EmailCampaign)
    for key, value in defaults.items():
        setattr(campaign, key, value)
    return campaign


class TestScheduleCampaign:
    """Tests for schedule_campaign service function."""

    @pytest.mark.asyncio
    async def test_schedules_draft_with_scheduled_at(self):
        """Draft campaign with scheduled_at transitions to SCHEDULED."""
        db = AsyncMock()
        campaign = _make_campaign(
            status=EmailCampaignStatus.DRAFT,
            scheduled_at=datetime(2026, 12, 31, tzinfo=UTC),
        )
        result = await schedule_campaign(db, campaign)
        assert campaign.status == EmailCampaignStatus.SCHEDULED
        assert result is campaign

    @pytest.mark.asyncio
    async def test_raises_if_not_draft(self):
        """Non-draft campaign raises ValueError."""
        db = AsyncMock()
        campaign = _make_campaign(
            status=EmailCampaignStatus.SENT,
            scheduled_at=datetime(2026, 12, 31, tzinfo=UTC),
        )
        with pytest.raises(ValueError, match="Only draft campaigns"):
            await schedule_campaign(db, campaign)

    @pytest.mark.asyncio
    async def test_raises_if_no_scheduled_at(self):
        """Draft campaign without scheduled_at raises ValueError."""
        db = AsyncMock()
        campaign = _make_campaign(status=EmailCampaignStatus.DRAFT, scheduled_at=None)
        with pytest.raises(ValueError, match="must have a scheduled_at time"):
            await schedule_campaign(db, campaign)


class TestCancelCampaign:
    """Tests for cancel_campaign service function."""

    @pytest.mark.asyncio
    async def test_cancels_draft_campaign(self):
        """Draft campaign transitions to CANCELLED."""
        db = AsyncMock()
        campaign = _make_campaign(status=EmailCampaignStatus.DRAFT)
        result = await cancel_campaign(db, campaign)
        assert campaign.status == EmailCampaignStatus.CANCELLED
        assert result is campaign

    @pytest.mark.asyncio
    async def test_cancels_scheduled_campaign(self):
        """Scheduled campaign can be cancelled."""
        db = AsyncMock()
        campaign = _make_campaign(status=EmailCampaignStatus.SCHEDULED)
        await cancel_campaign(db, campaign)
        assert campaign.status == EmailCampaignStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_raises_if_already_sent(self):
        """Already sent campaign raises ValueError."""
        db = AsyncMock()
        campaign = _make_campaign(status=EmailCampaignStatus.SENT)
        with pytest.raises(ValueError, match="Cannot cancel"):
            await cancel_campaign(db, campaign)

    @pytest.mark.asyncio
    async def test_raises_if_sending(self):
        """Campaign in SENDING state raises ValueError."""
        db = AsyncMock()
        campaign = _make_campaign(status=EmailCampaignStatus.SENDING)
        with pytest.raises(ValueError, match="Cannot cancel"):
            await cancel_campaign(db, campaign)


class TestInitiateSend:
    """Tests for initiate_send service function."""

    @pytest.mark.asyncio
    async def test_sends_draft_campaign(self):
        """Draft campaign transitions through SENDING to SENT."""
        db = AsyncMock()
        campaign = _make_campaign(status=EmailCampaignStatus.DRAFT)

        # Mock DB query returning 3 subscribed members
        member_result = MagicMock()
        member_result.scalars.return_value.all.return_value = [
            MagicMock(),
            MagicMock(),
            MagicMock(),
        ]
        db.execute = AsyncMock(return_value=member_result)

        result = await initiate_send(db, campaign)

        assert result["queued"] == 3
        assert campaign.status == EmailCampaignStatus.SENT
        assert campaign.total_recipients == 3
        assert campaign.sent_count == 3
        assert campaign.sent_at is not None

    @pytest.mark.asyncio
    async def test_raises_if_already_sent(self):
        """Already sent campaign raises ValueError."""
        db = AsyncMock()
        campaign = _make_campaign(status=EmailCampaignStatus.SENT)
        with pytest.raises(ValueError, match="Cannot send"):
            await initiate_send(db, campaign)

    @pytest.mark.asyncio
    async def test_zero_recipients(self):
        """Campaign with empty list sends with zero count."""
        db = AsyncMock()
        campaign = _make_campaign(status=EmailCampaignStatus.DRAFT)

        member_result = MagicMock()
        member_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=member_result)

        result = await initiate_send(db, campaign)
        assert result["queued"] == 0
        assert campaign.sent_count == 0


class TestGetPendingScheduledCampaigns:
    """Tests for get_pending_scheduled_campaigns service function."""

    @pytest.mark.asyncio
    async def test_returns_due_campaigns(self):
        """Returns campaigns with status=SCHEDULED and past scheduled_at."""
        db = AsyncMock()
        campaign = _make_campaign(
            status=EmailCampaignStatus.SCHEDULED,
            scheduled_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [campaign]
        db.execute = AsyncMock(return_value=result_mock)

        results = await get_pending_scheduled_campaigns(db)
        assert len(results) == 1
        assert results[0] is campaign
