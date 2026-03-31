"""Unit tests for email tracking service — open/click event recording and stats.

Tests:
- record_open state validation and event creation
- record_click state validation and redirect URL return
- get_campaign_stats aggregation and rate calculation
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.db.models.email_campaign import EmailCampaign, EmailCampaignStatus
from src.db.models.email_campaign_event import EventType
from src.services.email_tracking_service import (
    get_campaign_stats,
    record_click,
    record_open,
)

CAMPAIGN_ID = uuid4()


def _make_campaign(**overrides) -> MagicMock:
    defaults = {
        "id": CAMPAIGN_ID,
        "status": EmailCampaignStatus.SENT,
        "total_recipients": 100,
    }
    defaults.update(overrides)
    campaign = MagicMock(spec=EmailCampaign)
    for key, value in defaults.items():
        setattr(campaign, key, value)
    return campaign


class TestRecordOpen:
    """Tests for record_open service function."""

    @pytest.mark.asyncio
    async def test_records_open_for_sent_campaign(self) -> None:
        """Open event is created for a SENT campaign."""
        db = AsyncMock()
        campaign = _make_campaign(status=EmailCampaignStatus.SENT)
        db.get = AsyncMock(return_value=campaign)

        await record_open(db, campaign_id=CAMPAIGN_ID)

        db.add.assert_called_once()
        event = db.add.call_args[0][0]
        assert event.event_type == EventType.OPEN
        assert event.campaign_id == CAMPAIGN_ID

    @pytest.mark.asyncio
    async def test_records_open_for_sending_campaign(self) -> None:
        """Open event is also accepted for a SENDING campaign."""
        db = AsyncMock()
        campaign = _make_campaign(status=EmailCampaignStatus.SENDING)
        db.get = AsyncMock(return_value=campaign)

        await record_open(db, campaign_id=CAMPAIGN_ID)

        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_if_campaign_not_found(self) -> None:
        """ValueError when campaign does not exist."""
        db = AsyncMock()
        db.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="not found"):
            await record_open(db, campaign_id=CAMPAIGN_ID)

    @pytest.mark.asyncio
    async def test_raises_if_campaign_not_sent(self) -> None:
        """ValueError when campaign is still in draft state."""
        db = AsyncMock()
        campaign = _make_campaign(status=EmailCampaignStatus.DRAFT)
        db.get = AsyncMock(return_value=campaign)

        with pytest.raises(ValueError, match="tracking only accepted"):
            await record_open(db, campaign_id=CAMPAIGN_ID)

    @pytest.mark.asyncio
    async def test_stores_recipient_and_variant(self) -> None:
        """Recipient email and variant are stored on the event."""
        db = AsyncMock()
        campaign = _make_campaign(status=EmailCampaignStatus.SENT)
        db.get = AsyncMock(return_value=campaign)

        await record_open(
            db,
            campaign_id=CAMPAIGN_ID,
            recipient_email="donor@example.com",
            variant="a",
        )

        event = db.add.call_args[0][0]
        assert event.recipient_email == "donor@example.com"
        assert event.variant == "a"


class TestRecordClick:
    """Tests for record_click service function."""

    @pytest.mark.asyncio
    async def test_records_click_and_returns_url(self) -> None:
        """Click event is created and destination URL is returned."""
        db = AsyncMock()
        campaign = _make_campaign(status=EmailCampaignStatus.SENT)
        db.get = AsyncMock(return_value=campaign)

        target_url = "https://refugio.example.com/adopt"
        _event, redirect_url = await record_click(
            db, campaign_id=CAMPAIGN_ID, clicked_url=target_url
        )

        assert redirect_url == target_url
        db.add.assert_called_once()
        event = db.add.call_args[0][0]
        assert event.event_type == EventType.CLICK
        assert event.clicked_url == target_url

    @pytest.mark.asyncio
    async def test_raises_if_campaign_not_found(self) -> None:
        """ValueError when campaign does not exist."""
        db = AsyncMock()
        db.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="not found"):
            await record_click(db, campaign_id=CAMPAIGN_ID, clicked_url="https://example.com")

    @pytest.mark.asyncio
    async def test_raises_if_campaign_not_sent(self) -> None:
        """ValueError for draft campaigns."""
        db = AsyncMock()
        campaign = _make_campaign(status=EmailCampaignStatus.CANCELLED)
        db.get = AsyncMock(return_value=campaign)

        with pytest.raises(ValueError, match="tracking only accepted"):
            await record_click(db, campaign_id=CAMPAIGN_ID, clicked_url="https://example.com")


class TestGetCampaignStats:
    """Tests for get_campaign_stats service function."""

    @pytest.mark.asyncio
    async def test_returns_zero_stats_for_new_campaign(self) -> None:
        """Stats are all zero when no events exist."""
        db = AsyncMock()
        campaign = _make_campaign(status=EmailCampaignStatus.SENT, total_recipients=50)
        db.get = AsyncMock(return_value=campaign)

        # Both event_type queries return empty
        empty_result = MagicMock()
        empty_result.all.return_value = []
        db.execute = AsyncMock(return_value=empty_result)

        stats = await get_campaign_stats(db, campaign_id=CAMPAIGN_ID)

        assert stats["opens"] == 0
        assert stats["clicks"] == 0
        assert stats["open_rate"] == 0.0
        assert stats["click_rate"] == 0.0
        assert stats["total_recipients"] == 50

    @pytest.mark.asyncio
    async def test_raises_if_campaign_not_found(self) -> None:
        """ValueError when campaign does not exist."""
        db = AsyncMock()
        db.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="not found"):
            await get_campaign_stats(db, campaign_id=CAMPAIGN_ID)

    @pytest.mark.asyncio
    async def test_open_rate_zero_when_no_recipients(self) -> None:
        """open_rate is 0.0 when total_recipients is 0 (no division by zero)."""
        db = AsyncMock()
        campaign = _make_campaign(status=EmailCampaignStatus.SENT, total_recipients=0)
        db.get = AsyncMock(return_value=campaign)

        empty_result = MagicMock()
        empty_result.all.return_value = []
        db.execute = AsyncMock(return_value=empty_result)

        stats = await get_campaign_stats(db, campaign_id=CAMPAIGN_ID)

        assert stats["open_rate"] == 0.0
        assert stats["click_rate"] == 0.0
