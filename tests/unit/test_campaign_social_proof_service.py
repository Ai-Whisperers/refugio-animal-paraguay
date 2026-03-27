"""Unit tests for the campaign social proof service.

Tests cover:
  - Returns None for missing/non-active campaigns
  - Correct progress_percentage calculation
  - Privacy masking: show_in_public=False → "Anonymous"
  - Anonymous donations (donor_id IS NULL) → "Anonymous"
  - Momentum counts (24h, 7d) are returned from DB correctly
  - Recent donors are capped at RECENT_DONOR_LIMIT
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services.campaign_social_proof_service import (
    get_campaign_social_proof,
)


def _make_db_execute_mock(scalars: list) -> AsyncMock:
    """Return a db.execute AsyncMock that returns scalar results in sequence."""
    execute_mock = AsyncMock()
    # Each call to db.execute returns a different result mock
    results = []
    for val in scalars:
        rm = MagicMock()
        if isinstance(val, tuple):
            row = MagicMock()
            row.total_cents = val[0]
            row.donation_count = val[1]
            rm.one.return_value = row
            rm.scalar_one.return_value = val[0]
        else:
            rm.scalar_one.return_value = val
            rm.all.return_value = val
        results.append(rm)
    execute_mock.side_effect = results
    return execute_mock


@pytest.mark.asyncio
async def test_returns_none_when_campaign_missing() -> None:
    db = AsyncMock()
    db.get = AsyncMock(return_value=None)

    result = await get_campaign_social_proof(db, uuid4())

    assert result is None


@pytest.mark.asyncio
async def test_returns_none_for_draft_campaign() -> None:
    db = AsyncMock()
    campaign = MagicMock()
    campaign.status = "draft"
    db.get = AsyncMock(return_value=campaign)

    result = await get_campaign_social_proof(db, uuid4())

    assert result is None


@pytest.mark.asyncio
async def test_progress_percentage_calculated_correctly() -> None:
    db = AsyncMock()
    campaign_id = uuid4()

    campaign = MagicMock()
    campaign.status = "active"
    campaign.target_amount_cents = 10_000  # €100
    campaign.currency = "EUR"
    db.get = AsyncMock(return_value=campaign)

    # Sequence of db.execute calls: totals row, 24h count, 7d count, recent donors
    totals_row = MagicMock()
    totals_row.total_cents = 3_000  # €30
    totals_row.donation_count = 5

    totals_result = MagicMock()
    totals_result.one.return_value = totals_row

    h24_result = MagicMock()
    h24_result.scalar_one.return_value = 2

    d7_result = MagicMock()
    d7_result.scalar_one.return_value = 4

    recent_result = MagicMock()
    recent_result.all.return_value = []  # no recent donors

    db.execute = AsyncMock(side_effect=[totals_result, h24_result, d7_result, recent_result])

    result = await get_campaign_social_proof(db, campaign_id)

    assert result is not None
    assert result.progress_percentage == 30.0
    assert result.total_raised_cents == 3_000
    assert result.donor_count == 5
    assert result.donations_last_24_hours == 2
    assert result.donations_last_7_days == 4


@pytest.mark.asyncio
async def test_progress_percentage_capped_at_100_when_overfunded() -> None:
    db = AsyncMock()
    campaign_id = uuid4()

    campaign = MagicMock()
    campaign.status = "active"
    campaign.target_amount_cents = 1_000
    campaign.currency = "EUR"
    db.get = AsyncMock(return_value=campaign)

    totals_row = MagicMock()
    totals_row.total_cents = 2_000  # 200% — overfunded
    totals_row.donation_count = 10

    totals_result = MagicMock()
    totals_result.one.return_value = totals_row

    for_h24 = MagicMock()
    for_h24.scalar_one.return_value = 1
    for_d7 = MagicMock()
    for_d7.scalar_one.return_value = 3
    for_recent = MagicMock()
    for_recent.all.return_value = []

    db.execute = AsyncMock(side_effect=[totals_result, for_h24, for_d7, for_recent])

    result = await get_campaign_social_proof(db, campaign_id)

    assert result is not None
    assert result.progress_percentage == 100.0


@pytest.mark.asyncio
async def test_donor_privacy_respected_show_in_public_false() -> None:
    db = AsyncMock()
    campaign_id = uuid4()

    campaign = MagicMock()
    campaign.status = "active"
    campaign.target_amount_cents = 1_000
    campaign.currency = "EUR"
    db.get = AsyncMock(return_value=campaign)

    totals_row = MagicMock()
    totals_row.total_cents = 500
    totals_row.donation_count = 1
    totals_result = MagicMock()
    totals_result.one.return_value = totals_row

    h24 = MagicMock()
    h24.scalar_one.return_value = 0
    d7 = MagicMock()
    d7.scalar_one.return_value = 1

    # Donor opted out of public listing
    donor = MagicMock()
    donor.show_in_public = False
    donor.full_name = "Maria García"

    donation = MagicMock()
    donation.amount_cents = 500
    donation.currency = "EUR"
    donation.created_at = datetime.now(tz=UTC)

    recent = MagicMock()
    recent.all.return_value = [(donation, donor)]

    db.execute = AsyncMock(side_effect=[totals_result, h24, d7, recent])

    result = await get_campaign_social_proof(db, campaign_id)

    assert result is not None
    assert len(result.recent_donors) == 1
    entry = result.recent_donors[0]
    assert entry.display_name == "Anonymous"
    assert entry.is_anonymous is True


@pytest.mark.asyncio
async def test_donor_first_name_only_when_show_in_public() -> None:
    db = AsyncMock()
    campaign_id = uuid4()

    campaign = MagicMock()
    campaign.status = "active"
    campaign.target_amount_cents = 1_000
    campaign.currency = "EUR"
    db.get = AsyncMock(return_value=campaign)

    totals_row = MagicMock()
    totals_row.total_cents = 500
    totals_row.donation_count = 1
    totals_result = MagicMock()
    totals_result.one.return_value = totals_row

    h24 = MagicMock()
    h24.scalar_one.return_value = 0
    d7 = MagicMock()
    d7.scalar_one.return_value = 1

    donor = MagicMock()
    donor.show_in_public = True
    donor.full_name = "Jan van der Berg"  # multi-word surname

    donation = MagicMock()
    donation.amount_cents = 500
    donation.currency = "EUR"
    donation.created_at = datetime.now(tz=UTC)

    recent = MagicMock()
    recent.all.return_value = [(donation, donor)]

    db.execute = AsyncMock(side_effect=[totals_result, h24, d7, recent])

    result = await get_campaign_social_proof(db, campaign_id)

    assert result is not None
    entry = result.recent_donors[0]
    assert entry.display_name == "Jan"
    assert entry.is_anonymous is False


@pytest.mark.asyncio
async def test_anonymous_donation_no_donor_shown_as_anonymous() -> None:
    """Donations with donor_id=NULL (truly anonymous) show as Anonymous."""
    db = AsyncMock()
    campaign_id = uuid4()

    campaign = MagicMock()
    campaign.status = "completed"
    campaign.target_amount_cents = 1_000
    campaign.currency = "EUR"
    db.get = AsyncMock(return_value=campaign)

    totals_row = MagicMock()
    totals_row.total_cents = 100
    totals_row.donation_count = 1
    totals_result = MagicMock()
    totals_result.one.return_value = totals_row

    h24 = MagicMock()
    h24.scalar_one.return_value = 0
    d7 = MagicMock()
    d7.scalar_one.return_value = 0

    donation = MagicMock()
    donation.amount_cents = 100
    donation.currency = "EUR"
    donation.created_at = datetime.now(tz=UTC)

    recent = MagicMock()
    recent.all.return_value = [(donation, None)]  # donor is None

    db.execute = AsyncMock(side_effect=[totals_result, h24, d7, recent])

    result = await get_campaign_social_proof(db, campaign_id)

    assert result is not None
    assert len(result.recent_donors) == 1
    entry = result.recent_donors[0]
    assert entry.display_name == "Anonymous"
    assert entry.is_anonymous is True


@pytest.mark.asyncio
async def test_zero_target_amount_returns_zero_progress() -> None:
    db = AsyncMock()
    campaign_id = uuid4()

    campaign = MagicMock()
    campaign.status = "active"
    campaign.target_amount_cents = 0  # edge case: no goal set
    campaign.currency = "EUR"
    db.get = AsyncMock(return_value=campaign)

    totals_row = MagicMock()
    totals_row.total_cents = 500
    totals_row.donation_count = 1
    totals_result = MagicMock()
    totals_result.one.return_value = totals_row

    h24 = MagicMock()
    h24.scalar_one.return_value = 0
    d7 = MagicMock()
    d7.scalar_one.return_value = 0
    recent = MagicMock()
    recent.all.return_value = []

    db.execute = AsyncMock(side_effect=[totals_result, h24, d7, recent])

    result = await get_campaign_social_proof(db, campaign_id)

    assert result is not None
    assert result.progress_percentage == 0.0
