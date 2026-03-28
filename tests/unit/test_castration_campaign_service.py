"""Unit tests for castration campaign service.

Tests campaign creation, validation, status computation, partner clinic
management, and completed count increments.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.db.models.castration_campaign import (
    CAMPAIGN_STATUS_ACTIVE,
    CAMPAIGN_STATUS_COMPLETED,
    CAMPAIGN_STATUS_PLANNED,
    CastrationCampaign,
)
from src.services.castration_campaign_service import (
    MAX_DESCRIPTION_LENGTH,
    MAX_TITLE_LENGTH,
    MIN_DESCRIPTION_LENGTH,
    MIN_TITLE_LENGTH,
    CampaignNotFoundError,
    ClinicNotFoundError,
    InvalidCampaignError,
    validate_campaign_data,
)

# --- Helpers ---

TODAY = date.today()
FUTURE_START = TODAY + timedelta(days=10)
FUTURE_END = TODAY + timedelta(days=40)
PAST_START = TODAY - timedelta(days=40)
PAST_END = TODAY - timedelta(days=10)
ACTIVE_START = TODAY - timedelta(days=5)
ACTIVE_END = TODAY + timedelta(days=25)


def _make_campaign(**overrides) -> MagicMock:
    """Create a mock CastrationCampaign with defaults."""
    defaults = {
        "id": uuid4(),
        "title": "Castration Drive 2026",
        "description": "A campaign to castrate 100 dogs in Asuncion.",
        "goal_message": "Help us reach our goal!",
        "target_count": 100,
        "completed_count": 0,
        "target_area": "Asuncion",
        "start_date": FUTURE_START,
        "end_date": FUTURE_END,
        "created_by_id": uuid4(),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "partner_clinics": [],
    }
    defaults.update(overrides)
    campaign = MagicMock(spec=CastrationCampaign)
    for k, v in defaults.items():
        setattr(campaign, k, v)
    return campaign


def _mock_db() -> AsyncMock:
    """Create a mock async database session."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    db.get = AsyncMock()
    db.delete = AsyncMock()
    return db


# --- Validation Tests ---


class TestValidateCampaignData:
    """Tests for campaign data validation."""

    def _valid_data(self) -> dict:
        return {
            "title": "Valid Campaign Title",
            "description": "A valid description for the campaign.",
            "target_count": 50,
            "start_date": FUTURE_START,
            "end_date": FUTURE_END,
            "partner_clinic_ids": [uuid4()],
        }

    def test_valid_data_passes(self) -> None:
        validate_campaign_data(**self._valid_data())

    def test_title_too_short(self) -> None:
        data = self._valid_data()
        data["title"] = "Hi"
        with pytest.raises(InvalidCampaignError, match="Title"):
            validate_campaign_data(**data)

    def test_title_too_long(self) -> None:
        data = self._valid_data()
        data["title"] = "x" * (MAX_TITLE_LENGTH + 1)
        with pytest.raises(InvalidCampaignError, match="Title"):
            validate_campaign_data(**data)

    def test_empty_title(self) -> None:
        data = self._valid_data()
        data["title"] = ""
        with pytest.raises(InvalidCampaignError, match="Title"):
            validate_campaign_data(**data)

    def test_description_too_short(self) -> None:
        data = self._valid_data()
        data["description"] = "Short"
        with pytest.raises(InvalidCampaignError, match="Description"):
            validate_campaign_data(**data)

    def test_description_too_long(self) -> None:
        data = self._valid_data()
        data["description"] = "x" * (MAX_DESCRIPTION_LENGTH + 1)
        with pytest.raises(InvalidCampaignError, match="Description"):
            validate_campaign_data(**data)

    def test_target_count_zero(self) -> None:
        data = self._valid_data()
        data["target_count"] = 0
        with pytest.raises(InvalidCampaignError, match="Target count"):
            validate_campaign_data(**data)

    def test_target_count_negative(self) -> None:
        data = self._valid_data()
        data["target_count"] = -5
        with pytest.raises(InvalidCampaignError, match="Target count"):
            validate_campaign_data(**data)

    def test_end_date_before_start_date(self) -> None:
        data = self._valid_data()
        data["end_date"] = data["start_date"] - timedelta(days=1)
        with pytest.raises(InvalidCampaignError, match="End date"):
            validate_campaign_data(**data)

    def test_end_date_equal_start_date(self) -> None:
        data = self._valid_data()
        data["end_date"] = data["start_date"]
        with pytest.raises(InvalidCampaignError, match="End date"):
            validate_campaign_data(**data)

    def test_no_partner_clinics(self) -> None:
        data = self._valid_data()
        data["partner_clinic_ids"] = []
        with pytest.raises(InvalidCampaignError, match="partner clinic"):
            validate_campaign_data(**data)


# --- Status Computation Tests ---


class TestCampaignStatus:
    """Tests for campaign status property."""

    def test_planned_status(self) -> None:
        campaign = CastrationCampaign()
        campaign.start_date = FUTURE_START
        campaign.end_date = FUTURE_END
        campaign.target_count = 10
        campaign.completed_count = 0
        assert campaign.status == CAMPAIGN_STATUS_PLANNED

    def test_active_status(self) -> None:
        campaign = CastrationCampaign()
        campaign.start_date = ACTIVE_START
        campaign.end_date = ACTIVE_END
        campaign.target_count = 10
        campaign.completed_count = 0
        assert campaign.status == CAMPAIGN_STATUS_ACTIVE

    def test_completed_status(self) -> None:
        campaign = CastrationCampaign()
        campaign.start_date = PAST_START
        campaign.end_date = PAST_END
        campaign.target_count = 10
        campaign.completed_count = 0
        assert campaign.status == CAMPAIGN_STATUS_COMPLETED


# --- Progress Percent Tests ---


class TestProgressPercent:
    """Tests for progress percentage computation."""

    def test_zero_completed(self) -> None:
        campaign = CastrationCampaign()
        campaign.target_count = 100
        campaign.completed_count = 0
        assert campaign.progress_percent == 0

    def test_half_completed(self) -> None:
        campaign = CastrationCampaign()
        campaign.target_count = 100
        campaign.completed_count = 50
        assert campaign.progress_percent == 50

    def test_fully_completed(self) -> None:
        campaign = CastrationCampaign()
        campaign.target_count = 100
        campaign.completed_count = 100
        assert campaign.progress_percent == 100

    def test_over_target_capped(self) -> None:
        campaign = CastrationCampaign()
        campaign.target_count = 100
        campaign.completed_count = 150
        assert campaign.progress_percent == 100

    def test_zero_target(self) -> None:
        campaign = CastrationCampaign()
        campaign.target_count = 0
        campaign.completed_count = 0
        assert campaign.progress_percent == 0


# --- Exception Tests ---


class TestExceptions:
    """Tests for custom exceptions."""

    def test_campaign_not_found(self) -> None:
        cid = uuid4()
        error = CampaignNotFoundError(cid)
        assert error.campaign_id == cid
        assert str(cid) in error.message

    def test_invalid_campaign(self) -> None:
        error = InvalidCampaignError("bad title")
        assert "bad title" in error.message

    def test_clinic_not_found(self) -> None:
        cid = uuid4()
        error = ClinicNotFoundError(cid)
        assert error.clinic_id == cid
        assert str(cid) in error.message


# --- Constants Tests ---


class TestConstants:
    """Tests for module constants."""

    def test_title_length_bounds(self) -> None:
        assert MIN_TITLE_LENGTH == 5
        assert MAX_TITLE_LENGTH == 200

    def test_description_length_bounds(self) -> None:
        assert MIN_DESCRIPTION_LENGTH == 10
        assert MAX_DESCRIPTION_LENGTH == 1000

    def test_status_labels(self) -> None:
        assert CAMPAIGN_STATUS_PLANNED == "planned"
        assert CAMPAIGN_STATUS_ACTIVE == "active"
        assert CAMPAIGN_STATUS_COMPLETED == "completed"


# --- Service Function Tests ---


class TestCreateCastrationCampaign:
    """Tests for campaign creation service."""

    @pytest.mark.asyncio
    async def test_creates_campaign(self) -> None:
        from src.services.castration_campaign_service import create_castration_campaign

        db = _mock_db()
        clinic_id = uuid4()
        # Mock VetClinic exists
        db.get.return_value = MagicMock()

        await create_castration_campaign(
            db,
            title="Test Campaign",
            description="A test campaign description.",
            target_count=50,
            target_area="Asuncion",
            start_date=FUTURE_START,
            end_date=FUTURE_END,
            partner_clinic_ids=[clinic_id],
        )

        # Should call db.add at least twice (campaign + junction)
        assert db.add.call_count >= 2
        db.flush.assert_awaited()

    @pytest.mark.asyncio
    async def test_rejects_invalid_data(self) -> None:
        from src.services.castration_campaign_service import create_castration_campaign

        db = _mock_db()

        with pytest.raises(InvalidCampaignError):
            await create_castration_campaign(
                db,
                title="Hi",
                description="Too short",
                target_count=0,
                target_area="Asuncion",
                start_date=FUTURE_END,
                end_date=FUTURE_START,
                partner_clinic_ids=[],
            )

    @pytest.mark.asyncio
    async def test_rejects_missing_clinic(self) -> None:
        from src.services.castration_campaign_service import create_castration_campaign

        db = _mock_db()
        db.get.return_value = None  # Clinic not found

        with pytest.raises(ClinicNotFoundError):
            await create_castration_campaign(
                db,
                title="Valid Campaign Title",
                description="A valid description for testing.",
                target_count=50,
                target_area="Asuncion",
                start_date=FUTURE_START,
                end_date=FUTURE_END,
                partner_clinic_ids=[uuid4()],
            )


class TestGetCastrationCampaign:
    """Tests for fetching a single campaign."""

    @pytest.mark.asyncio
    async def test_returns_campaign(self) -> None:
        from src.services.castration_campaign_service import get_castration_campaign

        db = _mock_db()
        campaign = _make_campaign()
        db.get.return_value = campaign

        result = await get_castration_campaign(db, campaign.id)
        assert result == campaign

    @pytest.mark.asyncio
    async def test_raises_for_missing(self) -> None:
        from src.services.castration_campaign_service import get_castration_campaign

        db = _mock_db()
        db.get.return_value = None

        with pytest.raises(CampaignNotFoundError):
            await get_castration_campaign(db, uuid4())


class TestIncrementCompletedCount:
    """Tests for completed count increment."""

    @pytest.mark.asyncio
    async def test_increments_count(self) -> None:
        from src.services.castration_campaign_service import increment_completed_count

        db = _mock_db()
        campaign = _make_campaign(completed_count=5)
        db.get.return_value = campaign

        await increment_completed_count(db, campaign.id)
        assert campaign.completed_count == 6
        db.flush.assert_awaited()

    @pytest.mark.asyncio
    async def test_raises_for_missing(self) -> None:
        from src.services.castration_campaign_service import increment_completed_count

        db = _mock_db()
        db.get.return_value = None

        with pytest.raises(CampaignNotFoundError):
            await increment_completed_count(db, uuid4())
