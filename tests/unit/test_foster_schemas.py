"""Unit tests for foster profile model enums, constants, and API schemas (RAP-190)."""

import pytest
from pydantic import ValidationError
from src.api.foster import FosterApplyRequest, FosterReviewRequest
from src.db.models.foster_profile import (
    ANIMAL_TYPE_PREFERENCE_VALUES,
    FOSTER_MAX_ANIMALS_LIMIT,
    FOSTER_MOTIVATION_MIN_LENGTH,
    AnimalTypePreference,
    FosterStatus,
    HomeType,
)


class TestFosterStatusEnum:
    def test_all_expected_values_present(self) -> None:
        assert FosterStatus.PENDING == "pending"
        assert FosterStatus.APPROVED == "approved"
        assert FosterStatus.REJECTED == "rejected"
        assert FosterStatus.INACTIVE == "inactive"

    def test_enum_is_str(self) -> None:
        assert isinstance(FosterStatus.PENDING, str)

    def test_four_statuses(self) -> None:
        assert len(list(FosterStatus)) == 4


class TestHomeTypeEnum:
    def test_all_expected_values_present(self) -> None:
        assert HomeType.HOUSE_WITH_YARD == "house_with_yard"
        assert HomeType.HOUSE_WITHOUT_YARD == "house_without_yard"
        assert HomeType.APARTMENT == "apartment"
        assert HomeType.FARM == "farm"
        assert HomeType.OTHER == "other"

    def test_enum_is_str(self) -> None:
        assert isinstance(HomeType.APARTMENT, str)


class TestAnimalTypePreferenceEnum:
    def test_all_expected_values_present(self) -> None:
        assert AnimalTypePreference.DOGS == "dogs"
        assert AnimalTypePreference.CATS == "cats"
        assert AnimalTypePreference.SMALL_ANIMALS == "small_animals"
        assert AnimalTypePreference.ANY == "any"

    def test_animal_type_values_set(self) -> None:
        assert {"dogs", "cats", "small_animals", "any"} == ANIMAL_TYPE_PREFERENCE_VALUES


class TestFosterApplyRequest:
    def test_valid_minimal_application(self) -> None:
        req = FosterApplyRequest(
            motivation="I love animals and want to help while they find permanent homes."
        )
        assert req.motivation.startswith("I love")
        assert req.home_type == HomeType.APARTMENT
        assert req.has_outdoor_space is False
        assert req.has_other_pets is False
        assert req.max_animals == 1
        assert req.preferred_animal_types == []

    def test_valid_full_application(self) -> None:
        req = FosterApplyRequest(
            motivation="I have 10 years of experience with dogs and want to help stray animals.",
            experience_description="Raised 3 dogs from puppies.",
            home_type=HomeType.HOUSE_WITH_YARD,
            has_outdoor_space=True,
            has_other_pets=True,
            other_pets_description="Two adult cats, neutered.",
            max_animals=3,
            preferred_animal_types=[AnimalTypePreference.DOGS, AnimalTypePreference.CATS],
        )
        assert req.home_type == HomeType.HOUSE_WITH_YARD
        assert req.has_outdoor_space is True
        assert len(req.preferred_animal_types) == 2

    def test_motivation_too_short_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            FosterApplyRequest(motivation="Short")
        errors = exc_info.value.errors()
        assert any("motivation" in str(e["loc"]) for e in errors)

    def test_motivation_min_length_boundary(self) -> None:
        # Exactly at min length should succeed
        min_motivation = "x" * FOSTER_MOTIVATION_MIN_LENGTH
        req = FosterApplyRequest(motivation=min_motivation)
        assert len(req.motivation) == FOSTER_MOTIVATION_MIN_LENGTH

    def test_motivation_too_long_raises(self) -> None:
        with pytest.raises(ValidationError):
            FosterApplyRequest(motivation="x" * 2001)

    def test_max_animals_below_minimum_raises(self) -> None:
        with pytest.raises(ValidationError):
            FosterApplyRequest(
                motivation="I love animals and want to help temporarily.",
                max_animals=0,
            )

    def test_max_animals_above_maximum_raises(self) -> None:
        with pytest.raises(ValidationError):
            FosterApplyRequest(
                motivation="I love animals and want to help temporarily.",
                max_animals=FOSTER_MAX_ANIMALS_LIMIT + 1,
            )

    def test_max_animals_at_limit_is_valid(self) -> None:
        req = FosterApplyRequest(
            motivation="I love animals and want to help temporarily.",
            max_animals=FOSTER_MAX_ANIMALS_LIMIT,
        )
        assert req.max_animals == FOSTER_MAX_ANIMALS_LIMIT

    def test_invalid_home_type_raises(self) -> None:
        with pytest.raises(ValidationError):
            FosterApplyRequest(
                motivation="I love animals and want to help temporarily.",
                home_type="castle",  # type: ignore[arg-type]
            )

    def test_invalid_animal_type_preference_raises(self) -> None:
        with pytest.raises(ValidationError):
            FosterApplyRequest(
                motivation="I love animals and want to help temporarily.",
                preferred_animal_types=["fish"],  # type: ignore[list-item]
            )

    def test_other_pets_description_max_length(self) -> None:
        req = FosterApplyRequest(
            motivation="I love animals and want to help temporarily.",
            has_other_pets=True,
            other_pets_description="x" * 500,
        )
        assert len(req.other_pets_description or "") == 500  # type: ignore[arg-type]

    def test_other_pets_description_too_long_raises(self) -> None:
        with pytest.raises(ValidationError):
            FosterApplyRequest(
                motivation="I love animals and want to help temporarily.",
                other_pets_description="x" * 501,
            )


class TestFosterReviewRequest:
    def test_approve_without_reason(self) -> None:
        req = FosterReviewRequest(approved=True)
        assert req.approved is True
        assert req.rejection_reason is None

    def test_reject_with_reason(self) -> None:
        req = FosterReviewRequest(approved=False, rejection_reason="Unsuitable living conditions.")
        assert req.approved is False
        assert req.rejection_reason == "Unsuitable living conditions."

    def test_rejection_reason_too_long_raises(self) -> None:
        with pytest.raises(ValidationError):
            FosterReviewRequest(approved=False, rejection_reason="x" * 1001)

    def test_rejection_reason_at_max_length(self) -> None:
        req = FosterReviewRequest(approved=False, rejection_reason="x" * 1000)
        assert len(req.rejection_reason or "") == 1000  # type: ignore[arg-type]
