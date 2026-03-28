"""Unit tests for the smart matching service."""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from src.services.smart_matching_service import (
    DEFAULT_LIMIT,
    EXPERIENCE_BONUS,
    MANDATORY_MET_BONUS,
    MAX_LIMIT,
    MAX_MATCH_SCORE,
    MIN_MATCH_SCORE,
    NO_REQUIREMENTS_SCORE,
    PREFERRED_MET_BONUS,
    SIZE_PREFERENCE_BONUS,
    SPECIES_PREFERENCE_BONUS,
    AnimalMatch,
    MatchReason,
    _generate_match_reason,
    _score_animal,
    find_matches,
)

# --- Helpers ---


def _make_animal(
    species: str = "dog",
    breed: str | None = "Labrador",
    birth_date: date | None = None,
    size: str | None = "large",
    status: str = "available",
) -> MagicMock:
    """Create a mock Animal with realistic attributes."""
    animal = MagicMock()
    animal.id = uuid4()
    animal.name = "Buddy"
    animal.species = species
    animal.breed = breed
    animal.birth_date = birth_date
    animal.size = size
    animal.status = status
    animal.primary_photo_url = "https://example.com/buddy.jpg"
    return animal


def _make_requirement(
    requirement_type: str = "yard_required",
    value: dict | None = None,
    priority: str = "mandatory",
    is_mandatory: bool = True,
) -> MagicMock:
    """Create a mock AdoptionRequirement."""
    req = MagicMock()
    req.requirement_type = requirement_type
    req.value = value or {"yard": "required"}
    req.priority = priority
    req.is_mandatory = is_mandatory
    return req


# --- Test _generate_match_reason ---


class TestGenerateMatchReason:
    """Tests for _generate_match_reason."""

    def test_returns_none_when_not_met(self) -> None:
        result = _generate_match_reason("yard_required", met=False)
        assert result is None

    def test_returns_reason_for_yard(self) -> None:
        result = _generate_match_reason("yard_required", met=True)
        assert result == "Has a yard suitable for this animal"

    def test_returns_reason_for_experience(self) -> None:
        result = _generate_match_reason("experience_required", met=True)
        assert result == "Has required pet experience"

    def test_returns_reason_for_home_type(self) -> None:
        result = _generate_match_reason("home_type", met=True)
        assert result == "Home type is compatible"

    def test_returns_reason_for_max_hours_alone(self) -> None:
        result = _generate_match_reason("max_hours_alone", met=True)
        assert result == "Work schedule is compatible"

    def test_returns_reason_for_other_pets(self) -> None:
        result = _generate_match_reason("other_pets_ok", met=True)
        assert result == "Other pets situation is compatible"

    def test_returns_reason_for_housing_status(self) -> None:
        result = _generate_match_reason("housing_status", met=True)
        assert result == "Housing ownership is suitable"

    def test_returns_reason_for_income(self) -> None:
        result = _generate_match_reason("income_requirement", met=True)
        assert result == "Meets income requirements"

    def test_returns_reason_for_no_children(self) -> None:
        result = _generate_match_reason("no_children_under", met=True)
        assert result == "Household meets child age requirements"

    def test_returns_fallback_for_unknown_type(self) -> None:
        result = _generate_match_reason("custom_check", met=True)
        assert result == "Meets custom_check requirement"


# --- Test _score_animal ---


class TestScoreAnimal:
    """Tests for _score_animal."""

    @pytest.mark.asyncio
    async def test_no_requirements_returns_base_score(self) -> None:
        db = AsyncMock()
        animal = _make_animal()

        with patch(
            "src.services.smart_matching_service.get_animal_requirements",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = await _score_animal(db, animal, {})

        assert result.match_score == NO_REQUIREMENTS_SCORE
        assert "No specific requirements" in result.why_match[0]

    @pytest.mark.asyncio
    async def test_all_requirements_met_gives_high_score(self) -> None:
        db = AsyncMock()
        animal = _make_animal()

        req = _make_requirement(
            requirement_type="yard_required",
            value={"yard": "required"},
            priority="mandatory",
        )
        answers = {"yard_required": {"yard": "yes"}}

        with (
            patch(
                "src.services.smart_matching_service.get_animal_requirements",
                new_callable=AsyncMock,
                return_value=[req],
            ),
            patch(
                "src.services.smart_matching_service._REQUIREMENT_CHECKERS",
                {"yard_required": lambda val, ans: True},
            ),
        ):
            result = await _score_animal(db, animal, answers)

        # 100% base + MANDATORY_MET_BONUS
        assert result.match_score == min(MAX_MATCH_SCORE, 100 + MANDATORY_MET_BONUS)

    @pytest.mark.asyncio
    async def test_no_requirements_met_gives_zero_score(self) -> None:
        db = AsyncMock()
        animal = _make_animal()

        req = _make_requirement(
            requirement_type="yard_required",
            value={"yard": "required"},
            priority="mandatory",
        )
        answers = {"yard_required": {"yard": "no"}}

        with (
            patch(
                "src.services.smart_matching_service.get_animal_requirements",
                new_callable=AsyncMock,
                return_value=[req],
            ),
            patch(
                "src.services.smart_matching_service._REQUIREMENT_CHECKERS",
                {"yard_required": lambda val, ans: False},
            ),
        ):
            result = await _score_animal(db, animal, answers)

        assert result.match_score == 0
        assert result.why_match == []

    @pytest.mark.asyncio
    async def test_species_preference_bonus_applied(self) -> None:
        db = AsyncMock()
        animal = _make_animal(species="cat")

        answers = {"species_preference": {"value": "cat"}}

        with patch(
            "src.services.smart_matching_service.get_animal_requirements",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = await _score_animal(db, animal, answers)

        assert result.match_score == NO_REQUIREMENTS_SCORE + SPECIES_PREFERENCE_BONUS
        assert any("cat preference" in r for r in result.why_match)

    @pytest.mark.asyncio
    async def test_size_preference_bonus_applied(self) -> None:
        db = AsyncMock()
        animal = _make_animal(size="large")

        answers = {"size_preference": {"value": "large"}}

        with patch(
            "src.services.smart_matching_service.get_animal_requirements",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = await _score_animal(db, animal, answers)

        assert result.match_score == NO_REQUIREMENTS_SCORE + SIZE_PREFERENCE_BONUS
        assert any("Size matches" in r for r in result.why_match)

    @pytest.mark.asyncio
    async def test_preferred_requirement_gives_preferred_bonus(self) -> None:
        db = AsyncMock()
        animal = _make_animal()

        req = _make_requirement(
            requirement_type="yard_required",
            value={"yard": "preferred"},
            priority="preferred",
        )
        answers = {"yard_required": {"yard": "yes"}}

        with (
            patch(
                "src.services.smart_matching_service.get_animal_requirements",
                new_callable=AsyncMock,
                return_value=[req],
            ),
            patch(
                "src.services.smart_matching_service._REQUIREMENT_CHECKERS",
                {"yard_required": lambda val, ans: True},
            ),
        ):
            result = await _score_animal(db, animal, answers)

        # 100% base + PREFERRED_MET_BONUS
        assert result.match_score == min(MAX_MATCH_SCORE, 100 + PREFERRED_MET_BONUS)

    @pytest.mark.asyncio
    async def test_missing_answer_treated_as_not_met(self) -> None:
        db = AsyncMock()
        animal = _make_animal()

        req = _make_requirement(
            requirement_type="yard_required",
            value={"yard": "required"},
            priority="mandatory",
        )
        # No answers provided for yard_required
        answers: dict[str, dict] = {}

        with (
            patch(
                "src.services.smart_matching_service.get_animal_requirements",
                new_callable=AsyncMock,
                return_value=[req],
            ),
            patch(
                "src.services.smart_matching_service._REQUIREMENT_CHECKERS",
                {"yard_required": lambda val, ans: True},
            ),
        ):
            result = await _score_animal(db, animal, answers)

        assert result.match_score == 0

    @pytest.mark.asyncio
    async def test_unknown_checker_skipped(self) -> None:
        db = AsyncMock()
        animal = _make_animal()

        req = _make_requirement(
            requirement_type="unknown_type",
            value={},
            priority="mandatory",
        )
        answers = {"unknown_type": {"value": "test"}}

        with (
            patch(
                "src.services.smart_matching_service.get_animal_requirements",
                new_callable=AsyncMock,
                return_value=[req],
            ),
            patch(
                "src.services.smart_matching_service._REQUIREMENT_CHECKERS",
                {},
            ),
        ):
            result = await _score_animal(db, animal, answers)

        # No requirements counted (skipped), so 0/0 edge case = NO_REQUIREMENTS_SCORE
        # Actually: total_count=1, met_count=0 -> 0/1*100 = 0
        assert result.match_score == 0

    @pytest.mark.asyncio
    async def test_score_capped_at_max(self) -> None:
        db = AsyncMock()
        animal = _make_animal(species="dog", size="large")

        req = _make_requirement(
            requirement_type="yard_required",
            value={"yard": "required"},
            priority="mandatory",
        )
        # Answers that trigger all bonuses
        answers = {
            "yard_required": {"yard": "yes"},
            "species_preference": {"value": "dog"},
            "size_preference": {"value": "large"},
        }

        with (
            patch(
                "src.services.smart_matching_service.get_animal_requirements",
                new_callable=AsyncMock,
                return_value=[req],
            ),
            patch(
                "src.services.smart_matching_service._REQUIREMENT_CHECKERS",
                {"yard_required": lambda val, ans: True},
            ),
        ):
            result = await _score_animal(db, animal, answers)

        assert result.match_score <= MAX_MATCH_SCORE

    @pytest.mark.asyncio
    async def test_animal_fields_mapped_correctly(self) -> None:
        db = AsyncMock()
        animal = _make_animal(
            species="cat",
            breed="Siamese",
            birth_date=date(2023, 6, 15),
            size="small",
        )

        with patch(
            "src.services.smart_matching_service.get_animal_requirements",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = await _score_animal(db, animal, {})

        assert result.animal_id == animal.id
        assert result.name == "Buddy"
        assert result.species == "cat"
        assert result.breed == "Siamese"
        assert result.birth_date == date(2023, 6, 15)
        assert result.photo_url == "https://example.com/buddy.jpg"


# --- Test find_matches ---


class TestFindMatches:
    """Tests for find_matches."""

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_animals(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result

        result = await find_matches(db, answers={})

        assert result["animals"] == []
        assert result["total_count"] == 0

    @pytest.mark.asyncio
    async def test_returns_animals_sorted_by_score_desc(self) -> None:
        db = AsyncMock()
        animal1 = _make_animal(species="dog")
        animal2 = _make_animal(species="cat")

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [animal1, animal2]
        db.execute.return_value = mock_result

        # animal2 (cat) gets species bonus
        answers = {"species_preference": {"value": "cat"}}

        with patch(
            "src.services.smart_matching_service.get_animal_requirements",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = await find_matches(db, answers=answers)

        assert result["total_count"] == 2
        scores = [a["match_score"] for a in result["animals"]]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_pagination_with_limit(self) -> None:
        db = AsyncMock()
        animals = [_make_animal() for _ in range(5)]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = animals
        db.execute.return_value = mock_result

        with patch(
            "src.services.smart_matching_service.get_animal_requirements",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = await find_matches(db, answers={}, limit=2)

        assert len(result["animals"]) == 2
        assert result["total_count"] == 5

    @pytest.mark.asyncio
    async def test_pagination_with_offset(self) -> None:
        db = AsyncMock()
        animals = [_make_animal() for _ in range(5)]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = animals
        db.execute.return_value = mock_result

        with patch(
            "src.services.smart_matching_service.get_animal_requirements",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = await find_matches(db, answers={}, limit=10, offset=3)

        assert len(result["animals"]) == 2
        assert result["total_count"] == 5

    @pytest.mark.asyncio
    async def test_result_contains_expected_fields(self) -> None:
        db = AsyncMock()
        animal = _make_animal(birth_date=date(2024, 1, 15))

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [animal]
        db.execute.return_value = mock_result

        with patch(
            "src.services.smart_matching_service.get_animal_requirements",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = await find_matches(db, answers={})

        first = result["animals"][0]
        assert "id" in first
        assert "name" in first
        assert "species" in first
        assert "breed" in first
        assert "birth_date" in first
        assert "photo_url" in first
        assert "match_score" in first
        assert "why_match" in first
        assert first["birth_date"] == "2024-01-15"


# --- Test dataclasses ---


class TestDataclasses:
    """Tests for MatchReason and AnimalMatch dataclasses."""

    def test_match_reason_defaults(self) -> None:
        reason = MatchReason(reason="Compatible yard")
        assert reason.reason == "Compatible yard"
        assert reason.bonus_points == 0

    def test_match_reason_with_bonus(self) -> None:
        reason = MatchReason(reason="Species match", bonus_points=10)
        assert reason.bonus_points == 10

    def test_animal_match_defaults(self) -> None:
        aid = uuid4()
        match = AnimalMatch(
            animal_id=aid,
            name="Luna",
            species="cat",
            breed=None,
            birth_date=None,
            photo_url=None,
            match_score=75,
        )
        assert match.animal_id == aid
        assert match.why_match == []

    def test_animal_match_with_reasons(self) -> None:
        match = AnimalMatch(
            animal_id=uuid4(),
            name="Rex",
            species="dog",
            breed="German Shepherd",
            birth_date=date(2022, 3, 1),
            photo_url="https://example.com/rex.jpg",
            match_score=90,
            why_match=["Has a yard", "Species match"],
        )
        assert len(match.why_match) == 2


# --- Test constants ---


class TestConstants:
    """Tests for scoring constants."""

    def test_scoring_constants_are_positive(self) -> None:
        assert MANDATORY_MET_BONUS > 0
        assert PREFERRED_MET_BONUS > 0
        assert SPECIES_PREFERENCE_BONUS > 0
        assert SIZE_PREFERENCE_BONUS > 0
        assert EXPERIENCE_BONUS > 0

    def test_score_range(self) -> None:
        assert MIN_MATCH_SCORE == 0
        assert MAX_MATCH_SCORE == 100

    def test_default_pagination(self) -> None:
        assert DEFAULT_LIMIT == 10
        assert MAX_LIMIT == 50

    def test_no_requirements_score(self) -> None:
        assert NO_REQUIREMENTS_SCORE == 50
