"""Unit tests for pre-qualification scoring service.

Tests scoring engine, requirement checking, failure messages,
wait time estimation, and suggested animals.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.db.models.adoption_requirement import RequirementType
from src.services.pre_qualification_service import (
    MAX_SCORE,
    MIN_SCORE,
    AnimalNotFoundError,
    InvalidAnswersError,
    _check_experience_required,
    _check_home_type,
    _check_housing_status,
    _check_income_requirement,
    _check_max_hours_alone,
    _check_no_children_under,
    _check_other_pets_ok,
    _check_yard_answer,
    _estimate_wait_time,
    _generate_failure_message,
    score_answers,
)

# --- Helpers ---


def _make_requirement(**overrides) -> MagicMock:
    """Create a mock AdoptionRequirement with defaults."""
    defaults = {
        "id": uuid4(),
        "animal_id": None,
        "requirement_type": RequirementType.YARD_REQUIRED,
        "value": {"yard": "required"},
        "is_mandatory": True,
        "active": True,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    req = MagicMock()
    for k, v in defaults.items():
        setattr(req, k, v)
    return req


def _mock_db() -> AsyncMock:
    """Create a mock async database session."""
    db = AsyncMock()
    db.get = AsyncMock()
    db.execute = AsyncMock()
    return db


# --- Yard Checker Tests ---


class TestCheckYardAnswer:
    """Tests for yard requirement checking."""

    def test_required_with_yes(self) -> None:
        assert _check_yard_answer({"yard": "required"}, {"yard": "yes"}) is True

    def test_required_with_no(self) -> None:
        assert _check_yard_answer({"yard": "required"}, {"yard": "no"}) is False

    def test_preferred_always_passes(self) -> None:
        assert _check_yard_answer({"yard": "preferred"}, {"yard": "no"}) is True

    def test_not_needed_always_passes(self) -> None:
        assert _check_yard_answer({"yard": "not_needed"}, {"yard": "no"}) is True

    def test_required_with_missing_answer(self) -> None:
        assert _check_yard_answer({"yard": "required"}, {}) is False


# --- Children Age Checker Tests ---


class TestCheckNoChildrenUnder:
    """Tests for minimum child age requirement."""

    def test_no_children(self) -> None:
        assert _check_no_children_under({"age": 5}, {"youngest_child_age": None}) is True

    def test_child_old_enough(self) -> None:
        assert _check_no_children_under({"age": 5}, {"youngest_child_age": 6}) is True

    def test_child_exact_age(self) -> None:
        assert _check_no_children_under({"age": 5}, {"youngest_child_age": 5}) is True

    def test_child_too_young(self) -> None:
        assert _check_no_children_under({"age": 5}, {"youngest_child_age": 3}) is False

    def test_missing_answer(self) -> None:
        # No youngest_child_age key means no children
        assert _check_no_children_under({"age": 5}, {}) is True

    def test_invalid_type(self) -> None:
        assert _check_no_children_under({"age": 5}, {"youngest_child_age": "five"}) is False


# --- Experience Checker Tests ---


class TestCheckExperienceRequired:
    """Tests for experience level checking."""

    def test_none_required_none_provided(self) -> None:
        assert _check_experience_required({"level": "none"}, {"level": "none"}) is True

    def test_some_required_experienced_provided(self) -> None:
        assert _check_experience_required({"level": "some"}, {"level": "experienced"}) is True

    def test_experienced_required_some_provided(self) -> None:
        assert _check_experience_required({"level": "experienced"}, {"level": "some"}) is False

    def test_experienced_required_none_provided(self) -> None:
        assert _check_experience_required({"level": "experienced"}, {"level": "none"}) is False

    def test_missing_answer(self) -> None:
        # Missing level defaults to 0 rank
        assert _check_experience_required({"level": "some"}, {}) is False


# --- Home Type Checker Tests ---


class TestCheckHomeType:
    """Tests for home type requirement."""

    def test_matching_type(self) -> None:
        assert (
            _check_home_type({"types": ["apartment", "house"]}, {"home_type": "apartment"}) is True
        )

    def test_non_matching_type(self) -> None:
        assert _check_home_type({"types": ["house", "farm"]}, {"home_type": "apartment"}) is False

    def test_missing_answer(self) -> None:
        assert _check_home_type({"types": ["house"]}, {}) is False


# --- Hours Alone Checker Tests ---


class TestCheckMaxHoursAlone:
    """Tests for maximum hours alone requirement."""

    def test_within_limit(self) -> None:
        assert _check_max_hours_alone({"hours": 8}, {"hours_alone": 6}) is True

    def test_at_limit(self) -> None:
        assert _check_max_hours_alone({"hours": 8}, {"hours_alone": 8}) is True

    def test_over_limit(self) -> None:
        assert _check_max_hours_alone({"hours": 8}, {"hours_alone": 10}) is False

    def test_invalid_type(self) -> None:
        assert _check_max_hours_alone({"hours": 8}, {"hours_alone": "six"}) is False


# --- Other Pets Checker Tests ---


class TestCheckOtherPetsOk:
    """Tests for pet compatibility requirement."""

    def test_no_pets(self) -> None:
        assert _check_other_pets_ok({"pets": ["cats"]}, {"existing_pets": []}) is True

    def test_compatible_pets(self) -> None:
        assert _check_other_pets_ok({"pets": ["cats", "dogs"]}, {"existing_pets": ["cats"]}) is True

    def test_incompatible_pets(self) -> None:
        assert _check_other_pets_ok({"pets": ["cats"]}, {"existing_pets": ["dogs"]}) is False

    def test_missing_answer(self) -> None:
        # No existing_pets key means no pets
        assert _check_other_pets_ok({"pets": ["cats"]}, {}) is True


# --- Housing Status Checker Tests ---


class TestCheckHousingStatus:
    """Tests for housing status requirement."""

    def test_matching_status(self) -> None:
        assert _check_housing_status({"status": "owned"}, {"housing_status": "owned"}) is True

    def test_non_matching_status(self) -> None:
        assert _check_housing_status({"status": "owned"}, {"housing_status": "rented"}) is False


# --- Income Checker Tests ---


class TestCheckIncomeRequirement:
    """Tests for income requirement."""

    def test_meets_requirement(self) -> None:
        assert _check_income_requirement({"monthly": 50000}, {"monthly_income": 60000}) is True

    def test_exact_requirement(self) -> None:
        assert _check_income_requirement({"monthly": 50000}, {"monthly_income": 50000}) is True

    def test_below_requirement(self) -> None:
        assert _check_income_requirement({"monthly": 50000}, {"monthly_income": 30000}) is False

    def test_invalid_type(self) -> None:
        assert _check_income_requirement({"monthly": 50000}, {"monthly_income": "a lot"}) is False


# --- Scoring Engine Tests ---


class TestScoreAnswers:
    """Tests for the scoring engine."""

    def test_empty_requirements_gives_max_score(self) -> None:
        result = score_answers([], {})
        assert result.qualified is True
        assert result.score == MAX_SCORE

    def test_all_mandatory_met(self) -> None:
        reqs = [
            _make_requirement(
                requirement_type=RequirementType.YARD_REQUIRED,
                value={"yard": "required"},
                is_mandatory=True,
            ),
            _make_requirement(
                requirement_type=RequirementType.EXPERIENCE_REQUIRED,
                value={"level": "some"},
                is_mandatory=True,
            ),
        ]
        answers = {
            "yard_required": {"yard": "yes"},
            "experience_required": {"level": "experienced"},
        }
        result = score_answers(reqs, answers)
        assert result.qualified is True
        assert result.score == MAX_SCORE
        assert len(result.failed_requirements) == 0

    def test_mandatory_failed(self) -> None:
        reqs = [
            _make_requirement(
                requirement_type=RequirementType.YARD_REQUIRED,
                value={"yard": "required"},
                is_mandatory=True,
            ),
        ]
        answers = {"yard_required": {"yard": "no"}}
        result = score_answers(reqs, answers)
        assert result.qualified is False
        assert result.score == MIN_SCORE
        assert len(result.failed_requirements) == 1
        assert result.failed_requirements[0].is_mandatory is True

    def test_preferred_failed_still_qualified(self) -> None:
        reqs = [
            _make_requirement(
                requirement_type=RequirementType.YARD_REQUIRED,
                value={"yard": "required"},
                is_mandatory=True,
            ),
            _make_requirement(
                requirement_type=RequirementType.HOME_TYPE,
                value={"types": ["house"]},
                is_mandatory=False,
            ),
        ]
        answers = {
            "yard_required": {"yard": "yes"},
            "home_type": {"home_type": "apartment"},
        }
        result = score_answers(reqs, answers)
        assert result.qualified is True
        assert result.score == 50  # 1 of 2 met
        assert len(result.failed_requirements) == 1
        assert result.failed_requirements[0].is_mandatory is False

    def test_mixed_mandatory_and_preferred_failures(self) -> None:
        reqs = [
            _make_requirement(
                requirement_type=RequirementType.YARD_REQUIRED,
                value={"yard": "required"},
                is_mandatory=True,
            ),
            _make_requirement(
                requirement_type=RequirementType.EXPERIENCE_REQUIRED,
                value={"level": "experienced"},
                is_mandatory=True,
            ),
            _make_requirement(
                requirement_type=RequirementType.HOME_TYPE,
                value={"types": ["house"]},
                is_mandatory=False,
            ),
        ]
        answers = {
            "yard_required": {"yard": "yes"},
            "experience_required": {"level": "none"},
            "home_type": {"home_type": "apartment"},
        }
        result = score_answers(reqs, answers)
        assert result.qualified is False
        assert result.score == 33  # 1 of 3 met
        assert len(result.failed_requirements) == 2

    def test_missing_answers_treated_as_empty(self) -> None:
        reqs = [
            _make_requirement(
                requirement_type=RequirementType.YARD_REQUIRED,
                value={"yard": "required"},
                is_mandatory=True,
            ),
        ]
        # No answers provided at all
        result = score_answers(reqs, {})
        assert result.qualified is False
        assert result.score == MIN_SCORE

    def test_score_bounded(self) -> None:
        result = score_answers([], {})
        assert MIN_SCORE <= result.score <= MAX_SCORE


# --- Failure Message Tests ---


class TestGenerateFailureMessage:
    """Tests for human-readable failure messages."""

    def test_yard_failure_message(self) -> None:
        msg = _generate_failure_message(
            RequirementType.YARD_REQUIRED,
            {"yard": "required"},
            {"yard": "no"},
        )
        assert "yard" in msg.lower()
        assert "no" in msg

    def test_children_failure_message(self) -> None:
        msg = _generate_failure_message(
            RequirementType.NO_CHILDREN_UNDER,
            {"age": 5},
            {"youngest_child_age": 3},
        )
        assert "5" in msg
        assert "3" in msg

    def test_experience_failure_message(self) -> None:
        msg = _generate_failure_message(
            RequirementType.EXPERIENCE_REQUIRED,
            {"level": "experienced"},
            {"level": "none"},
        )
        assert "experienced" in msg
        assert "none" in msg

    def test_home_type_failure_message(self) -> None:
        msg = _generate_failure_message(
            RequirementType.HOME_TYPE,
            {"types": ["house", "farm"]},
            {"home_type": "apartment"},
        )
        assert "apartment" in msg

    def test_unknown_type_fallback(self) -> None:
        msg = _generate_failure_message("unknown_type", {}, {})
        assert "unknown_type" in msg


# --- Wait Time Estimation Tests ---


class TestEstimateWaitTime:
    """Tests for queue-based wait time estimation."""

    @pytest.mark.asyncio
    async def test_no_pending_requests(self) -> None:
        db = _mock_db()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 0
        db.execute.return_value = mock_result

        wait = await _estimate_wait_time(db, uuid4())
        assert "1-2 weeks" in wait

    @pytest.mark.asyncio
    async def test_with_pending_requests(self) -> None:
        db = _mock_db()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 3
        db.execute.return_value = mock_result

        wait = await _estimate_wait_time(db, uuid4())
        assert "4-5 weeks" in wait


# --- Exception Tests ---


class TestExceptions:
    """Tests for custom exceptions."""

    def test_animal_not_found(self) -> None:
        animal_id = uuid4()
        error = AnimalNotFoundError(animal_id)
        assert error.animal_id == animal_id
        assert str(animal_id) in error.message

    def test_invalid_answers(self) -> None:
        error = InvalidAnswersError(["missing yard", "bad type"])
        assert len(error.details) == 2
        assert "missing yard" in error.message


# --- Constants Tests ---


class TestConstants:
    """Tests for module constants."""

    def test_max_score(self) -> None:
        assert MAX_SCORE == 100

    def test_min_score(self) -> None:
        assert MIN_SCORE == 0
