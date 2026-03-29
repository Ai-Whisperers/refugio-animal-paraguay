"""Unit tests for adoption outcome service (RAP-260, EPIC-53)."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.db.models.adoption_outcome import AdoptionOutcomeType
from src.services.adoption_outcome_service import (
    AdoptionOutcomeNotFoundError,
    DuplicateAdoptionOutcomeError,
    OutcomeRecord,
    OutcomeStats,
    _record_to_dataclass,
    _safe_rate,
    create_outcome,
    get_outcome_by_adoption,
    get_outcome_by_id,
    get_outcome_stats,
    list_outcomes,
    update_outcome,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_outcome(**overrides):
    """Create a mock AdoptionOutcome ORM object."""
    now = datetime.now(UTC)
    defaults = {
        "id": uuid4(),
        "adoption_request_id": uuid4(),
        "outcome_type": "successful",
        "outcome_date": now,
        "notes": None,
        "avg_welfare_score": 4.5,
        "avg_satisfaction_score": 4.8,
        "total_follow_ups": 4,
        "completed_follow_ups": 3,
        "return_reason_code": None,
        "return_date": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    mock = MagicMock()
    for key, value in defaults.items():
        setattr(mock, key, value)
    return mock


def _make_db(scalar_value=None, scalars_values=None, execute_result=None):
    """Create a mock AsyncSession."""
    db = AsyncMock()
    db.scalar = AsyncMock(return_value=scalar_value)
    db.get = AsyncMock(return_value=scalar_value)
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()

    if scalars_values is not None:
        mock_result = MagicMock()
        mock_result.scalars.return_value = iter(scalars_values)
        db.execute = AsyncMock(return_value=mock_result)
    elif execute_result is not None:
        db.execute = AsyncMock(return_value=execute_result)
    return db


# ---------------------------------------------------------------------------
# _safe_rate
# ---------------------------------------------------------------------------


class TestSafeRate:
    def test_normal_rate(self):
        assert _safe_rate(3, 4) == 75.0

    def test_zero_denominator(self):
        assert _safe_rate(5, 0) == 0.0

    def test_full_rate(self):
        assert _safe_rate(10, 10) == 100.0

    def test_rounding(self):
        result = _safe_rate(1, 3)
        assert result == 33.33


# ---------------------------------------------------------------------------
# _record_to_dataclass
# ---------------------------------------------------------------------------


class TestRecordToDataclass:
    def test_maps_all_fields(self):
        mock_outcome = _make_outcome()
        record = _record_to_dataclass(mock_outcome)
        assert record.id == mock_outcome.id
        assert record.adoption_request_id == mock_outcome.adoption_request_id
        assert record.outcome_type == mock_outcome.outcome_type
        assert record.avg_welfare_score == mock_outcome.avg_welfare_score
        assert record.total_follow_ups == mock_outcome.total_follow_ups
        assert record.completed_follow_ups == mock_outcome.completed_follow_ups

    def test_maps_nullable_fields(self):
        mock_outcome = _make_outcome(
            notes=None,
            return_reason_code=None,
            return_date=None,
            avg_welfare_score=None,
            avg_satisfaction_score=None,
        )
        record = _record_to_dataclass(mock_outcome)
        assert record.notes is None
        assert record.return_reason_code is None
        assert record.avg_welfare_score is None


# ---------------------------------------------------------------------------
# create_outcome
# ---------------------------------------------------------------------------


class TestCreateOutcome:
    @pytest.mark.asyncio
    async def test_creates_successfully(self):
        adoption_request_id = uuid4()
        mock_outcome = _make_outcome(adoption_request_id=adoption_request_id)

        db = _make_db(scalar_value=None)

        async def mock_refresh(obj):
            for key, value in vars(mock_outcome).items():
                if not key.startswith("_"):
                    try:
                        setattr(obj, key, value)
                    except Exception:
                        pass

        db.refresh = AsyncMock(side_effect=mock_refresh)

        with patch(
            "src.services.adoption_outcome_service._sync_follow_up_scores",
            return_value=(4.5, 4.8, 4, 3),
        ):
            result = await create_outcome(
                db,
                adoption_request_id=adoption_request_id,
                outcome_type=AdoptionOutcomeType.SUCCESSFUL,
            )

        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_on_duplicate(self):
        adoption_request_id = uuid4()
        existing = _make_outcome(adoption_request_id=adoption_request_id)
        db = _make_db(scalar_value=existing)

        with pytest.raises(DuplicateAdoptionOutcomeError):
            await create_outcome(
                db,
                adoption_request_id=adoption_request_id,
                outcome_type=AdoptionOutcomeType.SUCCESSFUL,
            )

    @pytest.mark.asyncio
    async def test_sets_return_fields_for_returned_outcome(self):
        adoption_request_id = uuid4()
        return_date = datetime.now(UTC)
        mock_outcome = _make_outcome(
            adoption_request_id=adoption_request_id,
            outcome_type="returned",
            return_reason_code="behavior_issues",
            return_date=return_date,
        )

        db = _make_db(scalar_value=None)

        added_objects = []
        db.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))

        async def mock_refresh(obj):
            for attr in [
                "id", "adoption_request_id", "outcome_type", "outcome_date", "notes",
                "avg_welfare_score", "avg_satisfaction_score", "total_follow_ups",
                "completed_follow_ups", "return_reason_code", "return_date",
                "created_at", "updated_at",
            ]:
                setattr(obj, attr, getattr(mock_outcome, attr))

        db.refresh = AsyncMock(side_effect=mock_refresh)

        with patch(
            "src.services.adoption_outcome_service._sync_follow_up_scores",
            return_value=(None, None, 0, 0),
        ):
            result = await create_outcome(
                db,
                adoption_request_id=adoption_request_id,
                outcome_type=AdoptionOutcomeType.RETURNED,
                return_reason_code="behavior_issues",
                return_date=return_date,
            )

        assert len(added_objects) == 1
        created_obj = added_objects[0]
        assert created_obj.outcome_type == "returned"
        assert created_obj.return_reason_code == "behavior_issues"


# ---------------------------------------------------------------------------
# get_outcome_by_adoption
# ---------------------------------------------------------------------------


class TestGetOutcomeByAdoption:
    @pytest.mark.asyncio
    async def test_returns_outcome_when_found(self):
        adoption_request_id = uuid4()
        mock_outcome = _make_outcome(adoption_request_id=adoption_request_id)
        db = _make_db(scalar_value=mock_outcome)

        result = await get_outcome_by_adoption(db, adoption_request_id)

        assert isinstance(result, OutcomeRecord)
        assert result.adoption_request_id == adoption_request_id

    @pytest.mark.asyncio
    async def test_raises_when_not_found(self):
        db = _make_db(scalar_value=None)

        with pytest.raises(AdoptionOutcomeNotFoundError):
            await get_outcome_by_adoption(db, uuid4())


# ---------------------------------------------------------------------------
# get_outcome_by_id
# ---------------------------------------------------------------------------


class TestGetOutcomeById:
    @pytest.mark.asyncio
    async def test_returns_outcome(self):
        outcome_id = uuid4()
        mock_outcome = _make_outcome(id=outcome_id)
        db = _make_db(scalar_value=mock_outcome)

        result = await get_outcome_by_id(db, outcome_id)

        assert isinstance(result, OutcomeRecord)
        assert result.id == outcome_id

    @pytest.mark.asyncio
    async def test_raises_when_not_found(self):
        db = _make_db(scalar_value=None)

        with pytest.raises(AdoptionOutcomeNotFoundError):
            await get_outcome_by_id(db, uuid4())


# ---------------------------------------------------------------------------
# update_outcome
# ---------------------------------------------------------------------------


class TestUpdateOutcome:
    @pytest.mark.asyncio
    async def test_updates_outcome_type(self):
        adoption_request_id = uuid4()
        mock_outcome = _make_outcome(
            adoption_request_id=adoption_request_id,
            outcome_type="successful",
        )
        db = _make_db(scalar_value=mock_outcome)
        db.flush = AsyncMock()
        db.refresh = AsyncMock()

        with patch(
            "src.services.adoption_outcome_service._sync_follow_up_scores",
            return_value=(3.0, 4.0, 2, 2),
        ):
            result = await update_outcome(
                db,
                adoption_request_id=adoption_request_id,
                outcome_type=AdoptionOutcomeType.RETURNED,
                refresh_scores=True,
            )

        assert mock_outcome.outcome_type == "returned"

    @pytest.mark.asyncio
    async def test_raises_when_not_found(self):
        db = _make_db(scalar_value=None)

        with pytest.raises(AdoptionOutcomeNotFoundError):
            await update_outcome(db, uuid4(), outcome_type=AdoptionOutcomeType.SUCCESSFUL)

    @pytest.mark.asyncio
    async def test_skips_score_refresh_when_disabled(self):
        adoption_request_id = uuid4()
        mock_outcome = _make_outcome(adoption_request_id=adoption_request_id)
        db = _make_db(scalar_value=mock_outcome)
        db.flush = AsyncMock()
        db.refresh = AsyncMock()

        with patch(
            "src.services.adoption_outcome_service._sync_follow_up_scores"
        ) as mock_sync:
            await update_outcome(
                db,
                adoption_request_id=adoption_request_id,
                notes="Updated notes",
                refresh_scores=False,
            )
            mock_sync.assert_not_called()


# ---------------------------------------------------------------------------
# list_outcomes
# ---------------------------------------------------------------------------


class TestListOutcomes:
    @pytest.mark.asyncio
    async def test_returns_list(self):
        mock_outcomes = [_make_outcome(), _make_outcome()]
        db = _make_db(scalars_values=mock_outcomes)

        results = await list_outcomes(db)

        assert len(results) == 2
        assert all(isinstance(r, OutcomeRecord) for r in results)

    @pytest.mark.asyncio
    async def test_returns_empty_list(self):
        db = _make_db(scalars_values=[])

        results = await list_outcomes(db)

        assert results == []


# ---------------------------------------------------------------------------
# get_outcome_stats
# ---------------------------------------------------------------------------


class TestGetOutcomeStats:
    @pytest.mark.asyncio
    async def test_returns_stats(self):
        mock_row = MagicMock()
        mock_row.total = 10
        mock_row.successful = 7
        mock_row.returned = 2
        mock_row.rehomed = 1
        mock_row.deceased = 0
        mock_row.unknown = 0
        mock_row.avg_welfare = 4.2
        mock_row.avg_satisfaction = 4.6
        mock_row.avg_completion_rate = 75.0

        mock_result = MagicMock()
        mock_result.one.return_value = mock_row
        db = AsyncMock()
        db.execute = AsyncMock(return_value=mock_result)

        stats = await get_outcome_stats(db)

        assert isinstance(stats, OutcomeStats)
        assert stats.total_outcomes == 10
        assert stats.successful == 7
        assert stats.returned == 2
        assert stats.success_rate_pct == 70.0
        assert stats.return_rate_pct == 20.0
        assert stats.avg_welfare_score == 4.2
        assert stats.avg_satisfaction_score == 4.6
        assert stats.avg_followup_completion_rate_pct == 75.0

    @pytest.mark.asyncio
    async def test_handles_empty_database(self):
        mock_row = MagicMock()
        mock_row.total = 0
        mock_row.successful = 0
        mock_row.returned = 0
        mock_row.rehomed = 0
        mock_row.deceased = 0
        mock_row.unknown = 0
        mock_row.avg_welfare = None
        mock_row.avg_satisfaction = None
        mock_row.avg_completion_rate = None

        mock_result = MagicMock()
        mock_result.one.return_value = mock_row
        db = AsyncMock()
        db.execute = AsyncMock(return_value=mock_result)

        stats = await get_outcome_stats(db)

        assert stats.total_outcomes == 0
        assert stats.success_rate_pct == 0.0
        assert stats.return_rate_pct == 0.0
        assert stats.avg_welfare_score is None
        assert stats.avg_satisfaction_score is None
        assert stats.avg_followup_completion_rate_pct == 0.0

    @pytest.mark.asyncio
    async def test_generated_at_is_iso8601(self):
        mock_row = MagicMock()
        mock_row.total = 0
        mock_row.successful = 0
        mock_row.returned = 0
        mock_row.rehomed = 0
        mock_row.deceased = 0
        mock_row.unknown = 0
        mock_row.avg_welfare = None
        mock_row.avg_satisfaction = None
        mock_row.avg_completion_rate = None

        mock_result = MagicMock()
        mock_result.one.return_value = mock_row
        db = AsyncMock()
        db.execute = AsyncMock(return_value=mock_result)

        stats = await get_outcome_stats(db)

        datetime.fromisoformat(stats.generated_at)
