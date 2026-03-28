"""Unit tests for campaign-voucher integration service.

Tests milestone detection, voucher validation, campaign progress updates,
and stats retrieval.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from src.services.campaign_voucher_integration_service import (
    CASTRATION_SERVICE_CATEGORIES,
    MILESTONE_THRESHOLDS,
    VoucherNotLinkedError,
    _check_milestone,
    _milestone_label,
    handle_voucher_redeemed,
    is_castration_voucher_for_campaign,
)

# --- Helpers ---


def _mock_db() -> AsyncMock:
    """Create a mock async database session."""
    db = AsyncMock()
    db.get = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    return db


def _make_voucher(**overrides) -> MagicMock:
    """Create a mock VetVoucher."""
    defaults = {
        "id": uuid4(),
        "code": "VV-TEST1234",
        "status": "redeemed",
        "service_category": "castration_dog",
        "amount_pyg": 100000,
        "clinic_id": uuid4(),
    }
    defaults.update(overrides)
    voucher = MagicMock()
    for k, v in defaults.items():
        setattr(voucher, k, v)
    return voucher


def _make_campaign(**overrides) -> MagicMock:
    """Create a mock CastrationCampaign."""
    defaults = {
        "id": uuid4(),
        "title": "Test Campaign",
        "target_count": 100,
        "completed_count": 0,
        "progress_percent": 0,
        "status": "active",
        "partner_clinics": [],
    }
    defaults.update(overrides)
    campaign = MagicMock()
    for k, v in defaults.items():
        setattr(campaign, k, v)
    return campaign


# --- Milestone Detection Tests ---


class TestCheckMilestone:
    """Tests for milestone threshold crossing."""

    def test_no_milestone_at_zero(self) -> None:
        assert _check_milestone(0, 100) is None

    def test_25_percent_milestone(self) -> None:
        result = _check_milestone(25, 100)
        assert result == 0.25

    def test_50_percent_milestone(self) -> None:
        result = _check_milestone(50, 100)
        assert result == 0.50

    def test_75_percent_milestone(self) -> None:
        result = _check_milestone(75, 100)
        assert result == 0.75

    def test_100_percent_milestone(self) -> None:
        result = _check_milestone(100, 100)
        assert result == 1.0

    def test_no_milestone_between_thresholds(self) -> None:
        assert _check_milestone(30, 100) is None
        assert _check_milestone(60, 100) is None

    def test_zero_target_no_milestone(self) -> None:
        assert _check_milestone(5, 0) is None

    def test_small_target_milestones(self) -> None:
        # Target=4: milestones at 1 (25%), 2 (50%), 3 (75%), 4 (100%)
        assert _check_milestone(1, 4) == 0.25
        assert _check_milestone(2, 4) == 0.50
        assert _check_milestone(3, 4) == 0.75
        assert _check_milestone(4, 4) == 1.0


# --- Milestone Label Tests ---


class TestMilestoneLabel:
    """Tests for milestone label generation."""

    def test_25_percent(self) -> None:
        assert _milestone_label(0.25) == "25%"

    def test_50_percent(self) -> None:
        assert _milestone_label(0.50) == "50%"

    def test_100_percent(self) -> None:
        assert _milestone_label(1.0) == "100%"


# --- Voucher Validation Tests ---


class TestIsCastrationVoucherForCampaign:
    """Tests for voucher-campaign matching."""

    @pytest.mark.asyncio
    async def test_valid_castration_voucher(self) -> None:
        db = _mock_db()
        clinic_id = uuid4()
        voucher = _make_voucher(service_category="castration_dog", clinic_id=clinic_id)

        # Mock partner clinics query
        mock_result = MagicMock()
        mock_result.all.return_value = [(clinic_id,)]
        db.execute.return_value = mock_result

        result = await is_castration_voucher_for_campaign(db, voucher, uuid4())
        assert result is True

    @pytest.mark.asyncio
    async def test_non_castration_service(self) -> None:
        db = _mock_db()
        voucher = _make_voucher(service_category="vaccination")

        result = await is_castration_voucher_for_campaign(db, voucher, uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_wrong_clinic(self) -> None:
        db = _mock_db()
        voucher = _make_voucher(
            service_category="castration_cat",
            clinic_id=uuid4(),
        )

        # Mock partner clinics query - different clinic
        mock_result = MagicMock()
        mock_result.all.return_value = [(uuid4(),)]
        db.execute.return_value = mock_result

        result = await is_castration_voucher_for_campaign(db, voucher, uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_no_clinic_id(self) -> None:
        db = _mock_db()
        voucher = _make_voucher(
            service_category="castration_dog",
            clinic_id=None,
        )

        mock_result = MagicMock()
        mock_result.all.return_value = [(uuid4(),)]
        db.execute.return_value = mock_result

        result = await is_castration_voucher_for_campaign(db, voucher, uuid4())
        assert result is False


# --- Handle Voucher Redeemed Tests ---


class TestHandleVoucherRedeemed:
    """Tests for the main voucher redemption handler."""

    @pytest.mark.asyncio
    async def test_missing_voucher_raises(self) -> None:
        db = _mock_db()
        db.get.return_value = None

        with pytest.raises(VoucherNotLinkedError):
            await handle_voucher_redeemed(db, uuid4(), uuid4())

    @pytest.mark.asyncio
    async def test_non_redeemed_voucher_skipped(self) -> None:
        db = _mock_db()
        voucher = _make_voucher(status="purchased")
        db.get.return_value = voucher

        result = await handle_voucher_redeemed(db, voucher.id, uuid4())
        assert result["skipped"] is True
        assert result["reason"] == "voucher_not_redeemed"

    @pytest.mark.asyncio
    async def test_non_applicable_voucher_skipped(self) -> None:
        db = _mock_db()
        voucher = _make_voucher(service_category="vaccination")
        db.get.return_value = voucher

        result = await handle_voucher_redeemed(db, voucher.id, uuid4())
        assert result["skipped"] is True
        assert result["reason"] == "not_applicable"

    @pytest.mark.asyncio
    @patch("src.services.campaign_voucher_integration_service.increment_completed_count")
    @patch("src.services.campaign_voucher_integration_service.is_castration_voucher_for_campaign")
    async def test_successful_redemption(self, mock_check, mock_increment) -> None:
        db = _mock_db()
        campaign_id = uuid4()
        voucher = _make_voucher(status="redeemed", service_category="castration_dog")
        db.get.return_value = voucher

        mock_check.return_value = True
        mock_campaign = _make_campaign(completed_count=10, target_count=100, progress_percent=10)
        mock_increment.return_value = mock_campaign

        result = await handle_voucher_redeemed(db, voucher.id, campaign_id)

        assert result["skipped"] is False
        assert result["completed_count"] == 10
        mock_increment.assert_awaited_once_with(db, campaign_id)

    @pytest.mark.asyncio
    @patch("src.services.campaign_voucher_integration_service.increment_completed_count")
    @patch("src.services.campaign_voucher_integration_service.is_castration_voucher_for_campaign")
    async def test_milestone_detected(self, mock_check, mock_increment) -> None:
        db = _mock_db()
        campaign_id = uuid4()
        voucher = _make_voucher(status="redeemed", service_category="castration_dog")
        db.get.return_value = voucher

        mock_check.return_value = True
        # 25th out of 100 = 25% milestone
        mock_campaign = _make_campaign(completed_count=25, target_count=100, progress_percent=25)
        mock_increment.return_value = mock_campaign

        result = await handle_voucher_redeemed(db, voucher.id, campaign_id)

        assert result["skipped"] is False
        assert result.get("milestone") == "25%"

    @pytest.mark.asyncio
    @patch("src.services.campaign_voucher_integration_service.increment_completed_count")
    @patch("src.services.campaign_voucher_integration_service.is_castration_voucher_for_campaign")
    async def test_completion_detected(self, mock_check, mock_increment) -> None:
        db = _mock_db()
        campaign_id = uuid4()
        voucher = _make_voucher(status="redeemed", service_category="castration_cat")
        db.get.return_value = voucher

        mock_check.return_value = True
        mock_campaign = _make_campaign(completed_count=100, target_count=100, progress_percent=100)
        mock_increment.return_value = mock_campaign

        result = await handle_voucher_redeemed(db, voucher.id, campaign_id)

        assert result["skipped"] is False
        assert result["is_complete"] is True
        assert result.get("milestone") == "100%"


# --- Exception Tests ---


class TestExceptions:
    """Tests for custom exceptions."""

    def test_voucher_not_linked(self) -> None:
        vid = uuid4()
        error = VoucherNotLinkedError(vid)
        assert error.voucher_id == vid
        assert str(vid) in error.message


# --- Constants Tests ---


class TestConstants:
    """Tests for module constants."""

    def test_castration_categories(self) -> None:
        assert "castration_dog" in CASTRATION_SERVICE_CATEGORIES
        assert "castration_cat" in CASTRATION_SERVICE_CATEGORIES
        assert len(CASTRATION_SERVICE_CATEGORIES) == 2

    def test_milestone_thresholds(self) -> None:
        assert MILESTONE_THRESHOLDS == (0.25, 0.50, 0.75, 1.0)
