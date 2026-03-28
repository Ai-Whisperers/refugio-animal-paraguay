"""Unit tests for trial period management endpoints."""

from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.api.trial_periods import (
    CheckInRequest,
    TrialPeriodCreateRequest,
    TrialStatusUpdateRequest,
    _serialise_checkin,
    _serialise_trial,
    create_trial_period,
    get_trial_admin,
    get_trial_public,
    submit_check_in,
    update_trial_status,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_checkin(**overrides):
    """Build a mock TrialCheckIn."""
    c = MagicMock()
    c.id = overrides.get("id", uuid4())
    c.day_number = overrides.get("day_number", 3)
    c.how_is_animal = overrides.get("how_is_animal", "Happy and eating well")
    c.photos = overrides.get("photos", [])
    c.issues = overrides.get("issues")
    c.happiness_rating = overrides.get("happiness_rating", 4)
    c.has_issues = overrides.get("has_issues", False)
    c.created_at = overrides.get("created_at", datetime(2026, 3, 1, 12, 0, tzinfo=UTC))
    return c


def _make_trial(**overrides):
    """Build a mock TrialPeriod."""
    t = MagicMock()
    t.id = overrides.get("id", uuid4())
    t.adoption_request_id = overrides.get("adoption_request_id", uuid4())
    t.start_date = overrides.get("start_date", date(2026, 3, 1))
    t.end_date = overrides.get("end_date", date(2026, 3, 15))
    t.check_in_schedule = overrides.get("check_in_schedule", [{"day": 3, "status": "pending"}])
    t.status = overrides.get("status", "active")
    t.notes = overrides.get("notes")
    t.is_deleted = overrides.get("is_deleted", False)
    t.created_at = overrides.get("created_at", datetime(2026, 3, 1, 10, 0, tzinfo=UTC))
    t.updated_at = overrides.get("updated_at", datetime(2026, 3, 1, 10, 0, tzinfo=UTC))
    return t


def _mock_db():
    """Build an async mock database session."""
    db = AsyncMock()
    db.add = MagicMock()
    return db


def _fake_refresh_factory(**defaults):
    """Return an async refresh function that populates server-default fields."""

    async def fake_refresh(obj):
        if not hasattr(obj, "id") or obj.id is None:
            obj.id = defaults.get("id", uuid4())
        if not hasattr(obj, "created_at") or obj.created_at is None:
            obj.created_at = defaults.get("created_at", datetime(2026, 3, 1, 10, 0, tzinfo=UTC))
        if hasattr(obj, "updated_at") and obj.updated_at is None:
            obj.updated_at = defaults.get("updated_at", datetime(2026, 3, 1, 10, 0, tzinfo=UTC))

    return fake_refresh


# ---------------------------------------------------------------------------
# Test _serialise_checkin
# ---------------------------------------------------------------------------


class TestSerialiseCheckin:
    def test_all_fields(self):
        c = _make_checkin(
            day_number=7,
            how_is_animal="Very playful",
            photos=["photo1.jpg"],
            issues="Some barking",
            happiness_rating=3,
            has_issues=True,
        )
        result = _serialise_checkin(c)
        assert result["day_number"] == 7
        assert result["how_is_animal"] == "Very playful"
        assert result["photos"] == ["photo1.jpg"]
        assert result["issues"] == "Some barking"
        assert result["happiness_rating"] == 3
        assert result["has_issues"] is True
        assert "created_at" in result

    def test_none_photos_becomes_empty_list(self):
        c = _make_checkin(photos=None)
        result = _serialise_checkin(c)
        assert result["photos"] == []


# ---------------------------------------------------------------------------
# Test _serialise_trial
# ---------------------------------------------------------------------------


class TestSerialiseTrial:
    def test_all_fields(self):
        t = _make_trial(notes="Test notes")
        result = _serialise_trial(t)
        assert result["status"] == "active"
        assert result["notes"] == "Test notes"
        assert result["check_ins"] == []
        assert "start_date" in result
        assert "end_date" in result

    def test_with_check_ins(self):
        t = _make_trial()
        check_ins = [_make_checkin(), _make_checkin(day_number=7)]
        result = _serialise_trial(t, check_ins)
        assert len(result["check_ins"]) == 2

    def test_none_schedule_becomes_empty_list(self):
        t = _make_trial(check_in_schedule=None)
        result = _serialise_trial(t)
        assert result["check_in_schedule"] == []


# ---------------------------------------------------------------------------
# Test create_trial_period
# ---------------------------------------------------------------------------


class TestCreateTrialPeriod:
    @pytest.mark.asyncio
    async def test_creates_trial(self):
        adoption_id = uuid4()
        db = _mock_db()

        # Adoption exists
        adoption = MagicMock()
        db.get = AsyncMock(return_value=adoption)

        # No existing trial
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        trial_id = uuid4()
        db.refresh = _fake_refresh_factory(id=trial_id)

        payload = TrialPeriodCreateRequest()
        result = await create_trial_period(adoption_id, payload, db)

        assert result["status"] == "active"
        assert result["adoption_request_id"] == adoption_id
        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_404_adoption_not_found(self):
        db = _mock_db()
        db.get = AsyncMock(return_value=None)

        payload = TrialPeriodCreateRequest()
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await create_trial_period(uuid4(), payload, db)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_409_active_trial_exists(self):
        adoption_id = uuid4()
        db = _mock_db()

        adoption = MagicMock()
        db.get = AsyncMock(return_value=adoption)

        existing_trial = _make_trial(status="active")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_trial
        db.execute = AsyncMock(return_value=mock_result)

        payload = TrialPeriodCreateRequest()
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await create_trial_period(adoption_id, payload, db)
        assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# Test get_trial_admin
# ---------------------------------------------------------------------------


class TestGetTrialAdmin:
    @pytest.mark.asyncio
    async def test_returns_trial_with_checkins(self):
        adoption_id = uuid4()
        trial = _make_trial(adoption_request_id=adoption_id)
        checkin = _make_checkin()

        db = _mock_db()
        # First call: _get_trial_for_adoption, second: _get_check_ins
        mock_result_trial = MagicMock()
        mock_result_trial.scalar_one_or_none.return_value = trial
        mock_result_checkins = MagicMock()
        mock_result_checkins.scalars.return_value.all.return_value = [checkin]
        db.execute = AsyncMock(side_effect=[mock_result_trial, mock_result_checkins])

        result = await get_trial_admin(adoption_id, db)
        assert result["id"] == trial.id
        assert len(result["check_ins"]) == 1

    @pytest.mark.asyncio
    async def test_404_no_trial(self):
        db = _mock_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_trial_admin(uuid4(), db)
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Test update_trial_status
# ---------------------------------------------------------------------------


class TestUpdateTrialStatus:
    @pytest.mark.asyncio
    async def test_mark_passed(self):
        trial = _make_trial(status="active")
        db = _mock_db()

        mock_result_trial = MagicMock()
        mock_result_trial.scalar_one_or_none.return_value = trial
        mock_result_checkins = MagicMock()
        mock_result_checkins.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(side_effect=[mock_result_trial, mock_result_checkins])
        db.refresh = _fake_refresh_factory()

        payload = TrialStatusUpdateRequest(status="passed")
        result = await update_trial_status(uuid4(), payload, db)
        assert result["status"] == "passed"

    @pytest.mark.asyncio
    async def test_extend_adds_days(self):
        trial = _make_trial(
            status="active",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
            check_in_schedule=[{"day": 3, "status": "completed"}],
        )
        db = _mock_db()

        mock_result_trial = MagicMock()
        mock_result_trial.scalar_one_or_none.return_value = trial
        mock_result_checkins = MagicMock()
        mock_result_checkins.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(side_effect=[mock_result_trial, mock_result_checkins])
        db.refresh = _fake_refresh_factory()

        payload = TrialStatusUpdateRequest(status="extended", extend_days=7)
        result = await update_trial_status(uuid4(), payload, db)
        assert result["status"] == "extended"
        # End date extended by 7 days
        assert trial.end_date == date(2026, 3, 22)
        # New check-in day added to schedule
        assert len(result["check_in_schedule"]) == 2

    @pytest.mark.asyncio
    async def test_404_no_trial(self):
        db = _mock_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        payload = TrialStatusUpdateRequest(status="passed")
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await update_trial_status(uuid4(), payload, db)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_409_already_completed(self):
        trial = _make_trial(status="passed")
        db = _mock_db()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = trial
        db.execute = AsyncMock(return_value=mock_result)

        payload = TrialStatusUpdateRequest(status="failed")
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await update_trial_status(uuid4(), payload, db)
        assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# Test get_trial_public
# ---------------------------------------------------------------------------


class TestGetTrialPublic:
    @pytest.mark.asyncio
    async def test_returns_trial(self):
        trial = _make_trial()
        db = _mock_db()

        mock_result_trial = MagicMock()
        mock_result_trial.scalar_one_or_none.return_value = trial
        mock_result_checkins = MagicMock()
        mock_result_checkins.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(side_effect=[mock_result_trial, mock_result_checkins])

        result = await get_trial_public(uuid4(), db)
        assert result["id"] == trial.id

    @pytest.mark.asyncio
    async def test_404_no_trial(self):
        db = _mock_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_trial_public(uuid4(), db)
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Test submit_check_in
# ---------------------------------------------------------------------------


class TestSubmitCheckIn:
    @pytest.mark.asyncio
    async def test_creates_checkin(self):
        trial = _make_trial(
            status="active",
            start_date=date.today() - timedelta(days=3),
            check_in_schedule=[{"day": 3, "status": "pending"}],
        )
        db = _mock_db()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = trial
        db.execute = AsyncMock(return_value=mock_result)
        db.refresh = _fake_refresh_factory()

        payload = CheckInRequest(
            how_is_animal="Doing great, eating well",
            happiness_rating=5,
        )
        result = await submit_check_in(uuid4(), payload, db)
        assert result["day_number"] == 3
        assert result["happiness_rating"] == 5
        assert result["has_issues"] is False
        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_checkin_with_issues(self):
        trial = _make_trial(
            status="active",
            start_date=date.today() - timedelta(days=7),
            check_in_schedule=[{"day": 7, "status": "pending"}],
        )
        db = _mock_db()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = trial
        db.execute = AsyncMock(return_value=mock_result)
        db.refresh = _fake_refresh_factory()

        payload = CheckInRequest(
            how_is_animal="Some problems with feeding",
            issues="Won't eat dry food",
            happiness_rating=2,
        )
        result = await submit_check_in(uuid4(), payload, db)
        assert result["has_issues"] is True

    @pytest.mark.asyncio
    async def test_404_no_trial(self):
        db = _mock_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        payload = CheckInRequest(
            how_is_animal="Doing great, eating well",
            happiness_rating=5,
        )
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await submit_check_in(uuid4(), payload, db)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_409_trial_not_active(self):
        trial = _make_trial(status="passed")
        db = _mock_db()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = trial
        db.execute = AsyncMock(return_value=mock_result)

        payload = CheckInRequest(
            how_is_animal="Doing great, eating well",
            happiness_rating=5,
        )
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await submit_check_in(uuid4(), payload, db)
        assert exc_info.value.status_code == 409
