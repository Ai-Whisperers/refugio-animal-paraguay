"""Unit tests for adoption success scoring service."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from src.services.adoption_success_service import (
    GRADE_A_MIN,
    GRADE_A_PLUS_MIN,
    GRADE_B_MIN,
    MAX_SCORE,
    POINTS_FOLLOWUP_COMPLETED,
    POINTS_NO_ISSUES,
    POINTS_NO_RETURN,
    POINTS_PHOTO_SUBMITTED,
    POINTS_TRIAL_PASSED,
    AdoptionNotFoundError,
    AdoptionScoringError,
    calculate_adoption_score,
    calculate_grade,
    get_success_score_analytics,
    get_success_stories,
    grade_color,
)

# --- Test Error Classes ---


class TestErrorClasses:
    """Tests for error class hierarchy."""

    def test_adoption_scoring_error_is_exception(self) -> None:
        err = AdoptionScoringError("test")
        assert isinstance(err, Exception)

    def test_adoption_not_found_error_is_scoring_error(self) -> None:
        err = AdoptionNotFoundError("not found")
        assert isinstance(err, AdoptionScoringError)

    def test_adoption_not_found_error_message(self) -> None:
        err = AdoptionNotFoundError("Adoption abc not found")
        assert "abc" in str(err)


# --- Test Constants ---


class TestConstants:
    """Tests for scoring constants."""

    def test_max_score_is_100(self) -> None:
        assert MAX_SCORE == 100

    def test_points_sum_to_max(self) -> None:
        # With one follow-up completed, all bonuses should reach max
        # 20 + 10 + 5 + 30 + 20 = 85 (one followup)
        single_followup_max = (
            POINTS_FOLLOWUP_COMPLETED
            + POINTS_NO_ISSUES
            + POINTS_PHOTO_SUBMITTED
            + POINTS_NO_RETURN
            + POINTS_TRIAL_PASSED
        )
        assert single_followup_max == 85

    def test_grade_thresholds_descending(self) -> None:
        assert GRADE_A_PLUS_MIN > GRADE_A_MIN > GRADE_B_MIN


# --- Test calculate_grade ---


class TestCalculateGrade:
    """Tests for grade calculation."""

    def test_grade_a_plus_at_threshold(self) -> None:
        assert calculate_grade(GRADE_A_PLUS_MIN) == "A+"

    def test_grade_a_plus_above_threshold(self) -> None:
        assert calculate_grade(100) == "A+"

    def test_grade_a_at_threshold(self) -> None:
        assert calculate_grade(GRADE_A_MIN) == "A"

    def test_grade_a_below_a_plus(self) -> None:
        assert calculate_grade(GRADE_A_PLUS_MIN - 1) == "A"

    def test_grade_b_at_threshold(self) -> None:
        assert calculate_grade(GRADE_B_MIN) == "B"

    def test_grade_c_below_b(self) -> None:
        assert calculate_grade(GRADE_B_MIN - 1) == "C"

    def test_grade_c_at_zero(self) -> None:
        assert calculate_grade(0) == "C"


# --- Test grade_color ---


class TestGradeColor:
    """Tests for grade color mapping."""

    def test_a_plus_color(self) -> None:
        assert grade_color("A+") == "#22C55E"

    def test_a_color(self) -> None:
        assert grade_color("A") == "#3B82F6"

    def test_b_color(self) -> None:
        assert grade_color("B") == "#EAB308"

    def test_c_color(self) -> None:
        assert grade_color("C") == "#EF4444"

    def test_unknown_grade_returns_default(self) -> None:
        assert grade_color("D") == "#6B7280"


# --- Test calculate_adoption_score ---


def _make_followup(
    adoption_request_id=None,
    status="completed",
    issues_noted=None,
    photo_url=None,
):
    """Create a mock follow-up object."""
    fu = MagicMock()
    fu.adoption_request_id = adoption_request_id or uuid4()
    fu.status = status
    fu.issues_noted = issues_noted
    fu.photo_url = photo_url
    return fu


def _make_adoption(decided_at=None):
    """Create a mock adoption object."""
    adoption = MagicMock()
    adoption.id = uuid4()
    adoption.decided_at = decided_at
    return adoption


class TestCalculateAdoptionScore:
    """Tests for the main scoring function."""

    @pytest.mark.asyncio
    async def test_raises_not_found_for_missing_adoption(self) -> None:
        db = AsyncMock()
        # scalar_one_or_none returns None
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        with pytest.raises(AdoptionNotFoundError):
            await calculate_adoption_score(db, uuid4())

    @pytest.mark.asyncio
    async def test_score_with_no_followups_no_return_no_trial(self) -> None:
        adoption_id = uuid4()
        adoption = _make_adoption(decided_at=None)

        db = AsyncMock()
        # First call: adoption lookup
        adoption_result = MagicMock()
        adoption_result.scalar_one_or_none.return_value = adoption
        # Second call: follow-ups (empty)
        fu_result = MagicMock()
        fu_scalars = MagicMock()
        fu_scalars.all.return_value = []
        fu_result.scalars.return_value = fu_scalars
        # Third call: return count
        return_result = MagicMock()
        return_result.scalar_one.return_value = 0

        db.execute.side_effect = [adoption_result, fu_result, return_result]

        result = await calculate_adoption_score(db, adoption_id)

        # No followups: 0 points
        # No issues (vacuously true): +10
        # No photos: 0
        # No return: +30
        # No trial (no decided_at): 0
        assert result["score"] == 40
        assert result["grade"] == "C"
        assert result["followups_completed"] == 0
        assert result["followups_total"] == 0
        assert result["has_return"] is False

    @pytest.mark.asyncio
    async def test_score_with_completed_followup_and_photo(self) -> None:
        adoption_id = uuid4()
        adoption = _make_adoption(decided_at=None)
        fu = _make_followup(
            adoption_request_id=adoption_id,
            status="completed",
            issues_noted=None,
            photo_url="https://example.com/photo.jpg",
        )

        db = AsyncMock()
        adoption_result = MagicMock()
        adoption_result.scalar_one_or_none.return_value = adoption
        fu_result = MagicMock()
        fu_scalars = MagicMock()
        fu_scalars.all.return_value = [fu]
        fu_result.scalars.return_value = fu_scalars
        return_result = MagicMock()
        return_result.scalar_one.return_value = 0

        db.execute.side_effect = [adoption_result, fu_result, return_result]

        result = await calculate_adoption_score(db, adoption_id)

        # followup: 20, no_issues: 10, photo: 5, no_return: 30, trial: 0 = 65
        assert result["score"] == 65
        assert result["grade"] == "C"
        assert result["followups_completed"] == 1
        assert result["followups_total"] == 1

    @pytest.mark.asyncio
    async def test_score_with_trial_passed(self) -> None:
        adoption_id = uuid4()
        decided_at = datetime.now(UTC) - timedelta(days=91)
        adoption = _make_adoption(decided_at=decided_at)

        db = AsyncMock()
        adoption_result = MagicMock()
        adoption_result.scalar_one_or_none.return_value = adoption
        fu_result = MagicMock()
        fu_scalars = MagicMock()
        fu_scalars.all.return_value = []
        fu_result.scalars.return_value = fu_scalars
        return_result = MagicMock()
        return_result.scalar_one.return_value = 0

        db.execute.side_effect = [adoption_result, fu_result, return_result]

        result = await calculate_adoption_score(db, adoption_id)

        # no followups: 0, no_issues: 10, no photo: 0, no_return: 30, trial: 20 = 60
        assert result["score"] == 60
        assert result["breakdown"]["trial_passed"] == POINTS_TRIAL_PASSED

    @pytest.mark.asyncio
    async def test_score_with_return_request(self) -> None:
        adoption_id = uuid4()
        adoption = _make_adoption(decided_at=None)

        db = AsyncMock()
        adoption_result = MagicMock()
        adoption_result.scalar_one_or_none.return_value = adoption
        fu_result = MagicMock()
        fu_scalars = MagicMock()
        fu_scalars.all.return_value = []
        fu_result.scalars.return_value = fu_scalars
        return_result = MagicMock()
        return_result.scalar_one.return_value = 1  # has return

        db.execute.side_effect = [adoption_result, fu_result, return_result]

        result = await calculate_adoption_score(db, adoption_id)

        # no followups: 0, no_issues: 10, no photo: 0, has_return: 0, trial: 0 = 10
        assert result["score"] == 10
        assert result["has_return"] is True
        assert result["breakdown"]["no_return"] == 0

    @pytest.mark.asyncio
    async def test_score_with_issues_noted(self) -> None:
        adoption_id = uuid4()
        adoption = _make_adoption(decided_at=None)
        fu = _make_followup(
            adoption_request_id=adoption_id,
            status="completed",
            issues_noted="Animal seems anxious",
            photo_url=None,
        )

        db = AsyncMock()
        adoption_result = MagicMock()
        adoption_result.scalar_one_or_none.return_value = adoption
        fu_result = MagicMock()
        fu_scalars = MagicMock()
        fu_scalars.all.return_value = [fu]
        fu_result.scalars.return_value = fu_scalars
        return_result = MagicMock()
        return_result.scalar_one.return_value = 0

        db.execute.side_effect = [adoption_result, fu_result, return_result]

        result = await calculate_adoption_score(db, adoption_id)

        # followup: 20, issues: 0, no photo: 0, no_return: 30, trial: 0 = 50
        assert result["score"] == 50
        assert result["breakdown"]["no_issues"] == 0

    @pytest.mark.asyncio
    async def test_score_capped_at_max(self) -> None:
        """Multiple completed followups can exceed component sum but total is capped."""
        adoption_id = uuid4()
        decided_at = datetime.now(UTC) - timedelta(days=91)
        adoption = _make_adoption(decided_at=decided_at)

        # 5 completed followups = 100 points just from followups
        followups = [
            _make_followup(
                adoption_request_id=adoption_id,
                status="completed",
                issues_noted=None,
                photo_url="https://example.com/photo.jpg" if i == 0 else None,
            )
            for i in range(5)
        ]

        db = AsyncMock()
        adoption_result = MagicMock()
        adoption_result.scalar_one_or_none.return_value = adoption
        fu_result = MagicMock()
        fu_scalars = MagicMock()
        fu_scalars.all.return_value = followups
        fu_result.scalars.return_value = fu_scalars
        return_result = MagicMock()
        return_result.scalar_one.return_value = 0

        db.execute.side_effect = [adoption_result, fu_result, return_result]

        result = await calculate_adoption_score(db, adoption_id)

        assert result["score"] == MAX_SCORE
        assert result["grade"] == "A+"

    @pytest.mark.asyncio
    async def test_score_response_structure(self) -> None:
        adoption_id = uuid4()
        adoption = _make_adoption(decided_at=None)

        db = AsyncMock()
        adoption_result = MagicMock()
        adoption_result.scalar_one_or_none.return_value = adoption
        fu_result = MagicMock()
        fu_scalars = MagicMock()
        fu_scalars.all.return_value = []
        fu_result.scalars.return_value = fu_scalars
        return_result = MagicMock()
        return_result.scalar_one.return_value = 0

        db.execute.side_effect = [adoption_result, fu_result, return_result]

        result = await calculate_adoption_score(db, adoption_id)

        assert "adoption_request_id" in result
        assert "score" in result
        assert "grade" in result
        assert "grade_color" in result
        assert "breakdown" in result
        assert "followups_completed" in result
        assert "followups_total" in result
        assert "has_return" in result


# --- Test get_success_score_analytics ---


class TestGetSuccessScoreAnalytics:
    """Tests for aggregate analytics."""

    @pytest.mark.asyncio
    async def test_empty_when_no_adoptions(self) -> None:
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.__iter__ = MagicMock(return_value=iter([]))
        db.execute.return_value = result_mock

        result = await get_success_score_analytics(db)

        assert result["total_scored"] == 0
        assert result["average_score"] == 0.0
        assert result["grade_distribution"] == {"A+": 0, "A": 0, "B": 0, "C": 0}

    @pytest.mark.asyncio
    async def test_calculates_averages_for_multiple_adoptions(self) -> None:
        id1 = uuid4()
        id2 = uuid4()

        db = AsyncMock()
        # First call returns adoption IDs
        ids_result = MagicMock()
        ids_result.__iter__ = MagicMock(return_value=iter([(id1,), (id2,)]))
        db.execute.return_value = ids_result

        with patch("src.services.adoption_success_service.calculate_adoption_score") as mock_calc:
            mock_calc.side_effect = [
                {"score": 95, "grade": "A+"},
                {"score": 75, "grade": "B"},
            ]

            result = await get_success_score_analytics(db)

        assert result["total_scored"] == 2
        assert result["average_score"] == 85.0
        assert result["grade_distribution"]["A+"] == 1
        assert result["grade_distribution"]["B"] == 1

    @pytest.mark.asyncio
    async def test_skips_not_found_adoptions(self) -> None:
        id1 = uuid4()
        id2 = uuid4()

        db = AsyncMock()
        ids_result = MagicMock()
        ids_result.__iter__ = MagicMock(return_value=iter([(id1,), (id2,)]))
        db.execute.return_value = ids_result

        with patch("src.services.adoption_success_service.calculate_adoption_score") as mock_calc:
            mock_calc.side_effect = [
                AdoptionNotFoundError("not found"),
                {"score": 80, "grade": "A"},
            ]

            result = await get_success_score_analytics(db)

        assert result["total_scored"] == 1
        assert result["average_score"] == 80.0


# --- Test get_success_stories ---


class TestGetSuccessStories:
    """Tests for success stories retrieval."""

    @pytest.mark.asyncio
    async def test_empty_when_no_photo_adoptions(self) -> None:
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.__iter__ = MagicMock(return_value=iter([]))
        db.execute.return_value = result_mock

        result = await get_success_stories(db)

        assert result == []

    @pytest.mark.asyncio
    async def test_filters_by_min_score(self) -> None:
        id1 = uuid4()
        id2 = uuid4()

        db = AsyncMock()
        ids_result = MagicMock()
        ids_result.__iter__ = MagicMock(return_value=iter([(id1,), (id2,)]))
        db.execute.return_value = ids_result

        with patch("src.services.adoption_success_service.calculate_adoption_score") as mock_calc:
            mock_calc.side_effect = [
                {"score": 95, "grade": "A+"},  # above default 90
                {"score": 70, "grade": "B"},  # below default 90
            ]

            result = await get_success_stories(db, min_score=90)

        assert len(result) == 1
        assert result[0]["score"] == 95

    @pytest.mark.asyncio
    async def test_respects_limit(self) -> None:
        ids = [uuid4() for _ in range(5)]

        db = AsyncMock()
        ids_result = MagicMock()
        ids_result.__iter__ = MagicMock(return_value=iter([(i,) for i in ids]))
        db.execute.return_value = ids_result

        with patch("src.services.adoption_success_service.calculate_adoption_score") as mock_calc:
            mock_calc.side_effect = [
                {"score": 95, "grade": "A+"},
                {"score": 92, "grade": "A+"},
                {"score": 91, "grade": "A+"},
                {"score": 90, "grade": "A+"},
                {"score": 90, "grade": "A+"},
            ]

            result = await get_success_stories(db, min_score=90, limit=3)

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_sorted_by_score_descending(self) -> None:
        ids = [uuid4() for _ in range(3)]

        db = AsyncMock()
        ids_result = MagicMock()
        ids_result.__iter__ = MagicMock(return_value=iter([(i,) for i in ids]))
        db.execute.return_value = ids_result

        with patch("src.services.adoption_success_service.calculate_adoption_score") as mock_calc:
            mock_calc.side_effect = [
                {"score": 90, "grade": "A+"},
                {"score": 100, "grade": "A+"},
                {"score": 95, "grade": "A+"},
            ]

            result = await get_success_stories(db, min_score=90)

        assert result[0]["score"] == 100
        assert result[1]["score"] == 95
        assert result[2]["score"] == 90
