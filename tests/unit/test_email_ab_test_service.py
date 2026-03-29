"""Unit tests for email A/B test service — subject line variant splitting.

Tests:
- is_ab_test_active detection
- split_recipients_by_variant with various ratios
- initiate_send_ab state transitions and validation
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.db.models.email_campaign import EmailCampaign, EmailCampaignStatus
from src.services.email_ab_test_service import (
    initiate_send_ab,
    is_ab_test_active,
    split_recipients_by_variant,
)

CAMPAIGN_ID = uuid4()
LIST_ID = uuid4()


def _make_campaign(**overrides) -> MagicMock:
    defaults = {
        "id": CAMPAIGN_ID,
        "status": EmailCampaignStatus.DRAFT,
        "email_list_id": LIST_ID,
        "subject_a": "Subject A — adopt today",
        "subject_b": "Subject B — give a dog a home",
        "ab_ratio": 0.5,
        "total_recipients": 0,
        "sent_count": 0,
        "failed_count": 0,
        "sent_at": None,
    }
    defaults.update(overrides)
    campaign = MagicMock(spec=EmailCampaign)
    for key, value in defaults.items():
        setattr(campaign, key, value)
    return campaign


class TestIsAbTestActive:
    """Tests for is_ab_test_active helper."""

    def test_returns_true_when_subject_b_set(self) -> None:
        campaign = _make_campaign(subject_b="Variant B subject")
        assert is_ab_test_active(campaign) is True

    def test_returns_false_when_subject_b_none(self) -> None:
        campaign = _make_campaign(subject_b=None)
        assert is_ab_test_active(campaign) is False

    def test_returns_false_when_subject_b_empty_string(self) -> None:
        campaign = _make_campaign(subject_b="")
        assert is_ab_test_active(campaign) is False


class TestSplitRecipientsByVariant:
    """Tests for split_recipients_by_variant helper."""

    def test_50_50_split_even_number(self) -> None:
        members = list(range(10))
        a, b = split_recipients_by_variant(members, 0.5)
        assert len(a) == 5
        assert len(b) == 5

    def test_50_50_split_odd_number(self) -> None:
        """Odd total: variant A gets the extra member (ceil behaviour)."""
        members = list(range(11))
        a, b = split_recipients_by_variant(members, 0.5)
        assert len(a) == 6
        assert len(b) == 5
        assert len(a) + len(b) == 11

    def test_zero_ratio_assigns_all_to_b(self) -> None:
        members = list(range(10))
        a, b = split_recipients_by_variant(members, 0.0)
        assert len(a) == 0
        assert len(b) == 10

    def test_full_ratio_assigns_all_to_a(self) -> None:
        members = list(range(10))
        a, b = split_recipients_by_variant(members, 1.0)
        assert len(a) == 10
        assert len(b) == 0

    def test_empty_member_list(self) -> None:
        a, b = split_recipients_by_variant([], 0.5)
        assert a == []
        assert b == []

    def test_30_70_split(self) -> None:
        members = list(range(10))
        a, b = split_recipients_by_variant(members, 0.3)
        assert len(a) == 3
        assert len(b) == 7


class TestInitiateSendAb:
    """Tests for initiate_send_ab service function."""

    @pytest.mark.asyncio
    async def test_sends_draft_campaign_ab(self) -> None:
        """Draft A/B campaign transitions through SENDING to SENT."""
        db = AsyncMock()
        campaign = _make_campaign(status=EmailCampaignStatus.DRAFT)

        member_result = MagicMock()
        member_result.scalars.return_value.all.return_value = [
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
        ]
        db.execute = AsyncMock(return_value=member_result)

        result = await initiate_send_ab(db, campaign)

        assert result["queued"] == 4
        assert result["variant_a"] == 2
        assert result["variant_b"] == 2
        assert campaign.status == EmailCampaignStatus.SENT
        assert campaign.total_recipients == 4

    @pytest.mark.asyncio
    async def test_raises_if_already_sent(self) -> None:
        """Raises ValueError for a campaign already sent."""
        db = AsyncMock()
        campaign = _make_campaign(status=EmailCampaignStatus.SENT)

        with pytest.raises(ValueError, match="Cannot send"):
            await initiate_send_ab(db, campaign)

    @pytest.mark.asyncio
    async def test_raises_if_subject_a_missing(self) -> None:
        """Raises ValueError when subject_a is not set."""
        db = AsyncMock()
        campaign = _make_campaign(subject_a=None)

        with pytest.raises(ValueError, match="subject_a"):
            await initiate_send_ab(db, campaign)

    @pytest.mark.asyncio
    async def test_raises_if_subject_b_missing(self) -> None:
        """Raises ValueError when subject_b is not set (not an A/B campaign)."""
        db = AsyncMock()
        campaign = _make_campaign(subject_b=None)

        with pytest.raises(ValueError, match="subject_b"):
            await initiate_send_ab(db, campaign)

    @pytest.mark.asyncio
    async def test_zero_recipients(self) -> None:
        """Campaign with empty list sends with zero counts."""
        db = AsyncMock()
        campaign = _make_campaign(status=EmailCampaignStatus.DRAFT)

        member_result = MagicMock()
        member_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=member_result)

        result = await initiate_send_ab(db, campaign)
        assert result["queued"] == 0
        assert result["variant_a"] == 0
        assert result["variant_b"] == 0
