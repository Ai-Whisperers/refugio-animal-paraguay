"""Unit tests for foster placement matching service (RAP-191).

Tests the pure scoring logic (_score_foster_for_animal, _score_animal_for_foster,
_normalise_score) without database access.
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from typing import Any

from src.db.models.animal import AnimalSize, AnimalSpecies, AnimalStatus
from src.db.models.foster_profile import AnimalTypePreference, FosterStatus, HomeType
from src.services.foster_placement_service import (
    FOSTERABLE_STATUSES,
    RAW_MAX_SCORE,
    _normalise_score,
    _score_animal_for_foster,
    _score_foster_for_animal,
)

# ---------------------------------------------------------------------------
# Helpers — SimpleNamespace stand-ins for ORM objects
#
# SQLAlchemy mapped columns use descriptors that require the mapper to be
# attached to the instance.  The service functions only read plain attributes,
# so SimpleNamespace objects are a clean, zero-DB alternative.
# ---------------------------------------------------------------------------


def _make_profile(
    preferred_types: list[str] | None = None,
    home_type: str = HomeType.HOUSE_WITH_YARD,
    has_outdoor_space: bool = True,
    has_other_pets: bool = False,
    max_animals: int = 2,
    experience_description: str | None = "5 years fostering dogs",
    status: str = FosterStatus.APPROVED,
) -> Any:
    """Build a minimal foster profile namespace for testing (no DB required)."""
    return SimpleNamespace(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        motivation="I love animals and want to help.",
        experience_description=experience_description,
        home_type=home_type,
        has_outdoor_space=has_outdoor_space,
        has_other_pets=has_other_pets,
        other_pets_description=None,
        max_animals=max_animals,
        preferred_animal_types=(
            preferred_types if preferred_types is not None else [AnimalTypePreference.DOGS]
        ),
        status=status,
        rejection_reason=None,
        reviewed_by=None,
        reviewed_at=None,
    )


def _make_animal(
    species: str = AnimalSpecies.DOG,
    size: str | None = AnimalSize.MEDIUM,
    status: str = AnimalStatus.AVAILABLE,
) -> Any:
    """Build a minimal animal namespace for testing (no DB required)."""
    return SimpleNamespace(
        id=uuid.uuid4(),
        name="Buddy",
        species=species,
        size=size,
        status=status,
        breed=None,
        gender=None,
        birth_date=None,
        description=None,
        primary_photo_url=None,
        is_featured=False,
    )


# ---------------------------------------------------------------------------
# _normalise_score
# ---------------------------------------------------------------------------


class TestNormaliseScore:
    def test_zero_raw_score(self) -> None:
        assert _normalise_score(0) == 0

    def test_full_raw_score(self) -> None:
        assert _normalise_score(RAW_MAX_SCORE) == 100

    def test_half_raw_score_is_50(self) -> None:
        result = _normalise_score(RAW_MAX_SCORE // 2)
        assert 45 <= result <= 55  # Allow for rounding

    def test_clamped_above_max(self) -> None:
        assert _normalise_score(RAW_MAX_SCORE + 100) == 100

    def test_clamped_below_zero(self) -> None:
        assert _normalise_score(-50) == 0


# ---------------------------------------------------------------------------
# _score_foster_for_animal — capacity gate
# ---------------------------------------------------------------------------


class TestCapacityGate:
    def test_zero_remaining_capacity_gives_score_zero(self) -> None:
        profile = _make_profile(max_animals=2)
        animal = _make_animal()
        match = _score_foster_for_animal(profile, animal, current_placements=2)
        assert match.match_score == 0

    def test_at_capacity_why_not_message(self) -> None:
        profile = _make_profile(max_animals=1)
        animal = _make_animal()
        match = _score_foster_for_animal(profile, animal, current_placements=1)
        assert any("capacity" in msg.lower() for msg in match.why_not)

    def test_remaining_one_slot_is_eligible(self) -> None:
        profile = _make_profile(max_animals=2)
        animal = _make_animal()
        match = _score_foster_for_animal(profile, animal, current_placements=1)
        assert match.match_score > 0

    def test_capacity_info_in_why_match(self) -> None:
        profile = _make_profile(max_animals=3)
        animal = _make_animal()
        match = _score_foster_for_animal(profile, animal, current_placements=0)
        assert any("capacity" in msg.lower() or "3" in msg for msg in match.why_match)


# ---------------------------------------------------------------------------
# _score_foster_for_animal — species preference
# ---------------------------------------------------------------------------


class TestSpeciesPreference:
    def test_dog_matches_dogs_preference(self) -> None:
        profile = _make_profile(preferred_types=[AnimalTypePreference.DOGS])
        animal = _make_animal(species=AnimalSpecies.DOG)
        match = _score_foster_for_animal(profile, animal, current_placements=0)
        assert any("dog" in msg.lower() or "prefer" in msg.lower() for msg in match.why_match)

    def test_cat_matches_cats_preference(self) -> None:
        profile = _make_profile(preferred_types=[AnimalTypePreference.CATS])
        animal = _make_animal(species=AnimalSpecies.CAT)
        match = _score_foster_for_animal(profile, animal, current_placements=0)
        assert any("cat" in msg.lower() or "prefer" in msg.lower() for msg in match.why_match)

    def test_any_preference_matches_all_species(self) -> None:
        for species in (AnimalSpecies.DOG, AnimalSpecies.CAT, AnimalSpecies.OTHER):
            profile = _make_profile(preferred_types=[AnimalTypePreference.ANY])
            animal = _make_animal(species=species)
            match = _score_foster_for_animal(profile, animal, current_placements=0)
            assert any(
                "any" in msg.lower() for msg in match.why_match
            ), f"Failed for species={species}"

    def test_mismatched_species_adds_why_not_note(self) -> None:
        profile = _make_profile(preferred_types=[AnimalTypePreference.CATS])
        animal = _make_animal(species=AnimalSpecies.DOG)
        match = _score_foster_for_animal(profile, animal, current_placements=0)
        assert any("dog" in msg.lower() or "not list" in msg.lower() for msg in match.why_not)


# ---------------------------------------------------------------------------
# _score_foster_for_animal — outdoor space
# ---------------------------------------------------------------------------


class TestOutdoorSpace:
    def test_outdoor_space_bonus_for_dog(self) -> None:
        profile_with = _make_profile(has_outdoor_space=True)
        profile_without = _make_profile(has_outdoor_space=False)
        animal = _make_animal(species=AnimalSpecies.DOG)
        score_with = _score_foster_for_animal(
            profile_with, animal, current_placements=0
        ).match_score
        score_without = _score_foster_for_animal(
            profile_without, animal, current_placements=0
        ).match_score
        assert score_with > score_without

    def test_outdoor_space_bonus_for_large_animal(self) -> None:
        profile_with = _make_profile(has_outdoor_space=True)
        profile_without = _make_profile(has_outdoor_space=False)
        animal = _make_animal(species=AnimalSpecies.OTHER, size=AnimalSize.LARGE)
        score_with = _score_foster_for_animal(
            profile_with, animal, current_placements=0
        ).match_score
        score_without = _score_foster_for_animal(
            profile_without, animal, current_placements=0
        ).match_score
        assert score_with > score_without

    def test_no_outdoor_space_for_dog_adds_why_not(self) -> None:
        profile = _make_profile(has_outdoor_space=False)
        animal = _make_animal(species=AnimalSpecies.DOG)
        match = _score_foster_for_animal(profile, animal, current_placements=0)
        assert any("outdoor" in msg.lower() for msg in match.why_not)

    def test_outdoor_space_smaller_bonus_for_small_cat(self) -> None:
        profile = _make_profile(
            has_outdoor_space=True,
            preferred_types=[AnimalTypePreference.CATS],
        )
        animal = _make_animal(species=AnimalSpecies.CAT, size=AnimalSize.SMALL)
        match = _score_foster_for_animal(profile, animal, current_placements=0)
        # Partial bonus is still applied — family should get some credit
        assert match.match_score > 0


# ---------------------------------------------------------------------------
# _score_foster_for_animal — other pets
# ---------------------------------------------------------------------------


class TestOtherPets:
    def test_no_other_pets_gives_bonus(self) -> None:
        profile_no_pets = _make_profile(has_other_pets=False)
        profile_has_pets = _make_profile(has_other_pets=True)
        animal = _make_animal()
        score_no_pets = _score_foster_for_animal(
            profile_no_pets, animal, current_placements=0
        ).match_score
        score_has_pets = _score_foster_for_animal(
            profile_has_pets, animal, current_placements=0
        ).match_score
        assert score_no_pets > score_has_pets

    def test_has_other_pets_adds_why_not_note(self) -> None:
        profile = _make_profile(has_other_pets=True)
        animal = _make_animal()
        match = _score_foster_for_animal(profile, animal, current_placements=0)
        assert any("pet" in msg.lower() for msg in match.why_not)


# ---------------------------------------------------------------------------
# _score_foster_for_animal — experience
# ---------------------------------------------------------------------------


class TestExperience:
    def test_experience_adds_bonus(self) -> None:
        profile_with_exp = _make_profile(experience_description="10 years with dogs")
        profile_no_exp = _make_profile(experience_description=None)
        animal = _make_animal()
        score_with = _score_foster_for_animal(
            profile_with_exp, animal, current_placements=0
        ).match_score
        score_without = _score_foster_for_animal(
            profile_no_exp, animal, current_placements=0
        ).match_score
        assert score_with > score_without

    def test_blank_experience_not_awarded_bonus(self) -> None:
        profile = _make_profile(experience_description="   ")
        animal = _make_animal()
        match = _score_foster_for_animal(profile, animal, current_placements=0)
        assert not any("experience" in msg.lower() for msg in match.why_match)


# ---------------------------------------------------------------------------
# _score_foster_for_animal — field presence
# ---------------------------------------------------------------------------


class TestMatchFieldPresence:
    def test_match_contains_all_required_fields(self) -> None:
        profile = _make_profile()
        animal = _make_animal()
        match = _score_foster_for_animal(profile, animal, current_placements=0)
        assert match.foster_profile_id == profile.id
        assert match.user_id == profile.user_id
        assert match.home_type == profile.home_type
        assert match.has_outdoor_space == profile.has_outdoor_space
        assert match.has_other_pets == profile.has_other_pets
        assert match.max_animals == profile.max_animals
        assert match.current_placements == 0
        assert isinstance(match.match_score, int)
        assert 0 <= match.match_score <= 100
        assert isinstance(match.why_match, list)
        assert isinstance(match.why_not, list)


# ---------------------------------------------------------------------------
# _score_animal_for_foster
# ---------------------------------------------------------------------------


class TestScoreAnimalForFoster:
    def test_symmetric_scores_with_score_foster_for_animal(self) -> None:
        profile = _make_profile()
        animal = _make_animal()
        foster_match = _score_foster_for_animal(profile, animal, current_placements=0)
        animal_match = _score_animal_for_foster(profile, animal, current_placements=0)
        assert foster_match.match_score == animal_match.match_score

    def test_animal_match_contains_animal_fields(self) -> None:
        profile = _make_profile()
        animal = _make_animal()
        match = _score_animal_for_foster(profile, animal, current_placements=0)
        assert match.animal_id == animal.id
        assert match.name == animal.name
        assert match.species == animal.species
        assert match.size == animal.size
        assert 0 <= match.match_score <= 100

    def test_at_capacity_returns_zero_for_animal(self) -> None:
        profile = _make_profile(max_animals=1)
        animal = _make_animal()
        match = _score_animal_for_foster(profile, animal, current_placements=1)
        assert match.match_score == 0


# ---------------------------------------------------------------------------
# FOSTERABLE_STATUSES
# ---------------------------------------------------------------------------


class TestFosterableStatuses:
    def test_intake_is_fosterable(self) -> None:
        assert AnimalStatus.INTAKE in FOSTERABLE_STATUSES

    def test_available_is_fosterable(self) -> None:
        assert AnimalStatus.AVAILABLE in FOSTERABLE_STATUSES

    def test_quarantine_is_fosterable(self) -> None:
        assert AnimalStatus.QUARANTINE in FOSTERABLE_STATUSES

    def test_under_treatment_is_fosterable(self) -> None:
        assert AnimalStatus.UNDER_TREATMENT in FOSTERABLE_STATUSES

    def test_adopted_not_fosterable(self) -> None:
        assert AnimalStatus.ADOPTED not in FOSTERABLE_STATUSES

    def test_foster_not_in_fosterable(self) -> None:
        # Already fostered — shouldn't be matched again
        assert AnimalStatus.FOSTER not in FOSTERABLE_STATUSES
