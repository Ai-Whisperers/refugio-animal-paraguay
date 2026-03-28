"""Service for pre-qualification scoring of adopter answers against requirements.

Evaluates adopter responses, computes qualification status + score,
generates failure messages, and suggests matching animals.
"""

from __future__ import annotations

import logging
import typing
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.adoption_request import AdoptionRequest, AdoptionRequestStatus
from src.db.models.adoption_requirement import (
    REQUIREMENT_DESCRIPTIONS,
    AdoptionRequirement,
    RequirementType,
)
from src.db.models.animal import Animal, AnimalStatus
from src.services.adoption_requirement_service import get_animal_requirements

logger = logging.getLogger(__name__)

# Scoring constants
MANDATORY_MET_POINTS = 5
PREFERRED_MET_POINTS = 10
MAX_SCORE = 100
MIN_SCORE = 0

# Suggested animals limits
MAX_SUGGESTED_ANIMALS = 10

# Wait time estimation constants (weeks per pending request ahead in queue)
WEEKS_PER_PENDING_REQUEST = 1
BASE_WAIT_WEEKS = 1


class AnimalNotFoundError(Exception):
    """Raised when the target animal does not exist or is not available."""

    def __init__(self, animal_id: UUID) -> None:
        self.animal_id = animal_id
        self.message = f"Animal {animal_id} not found or not available for adoption."
        super().__init__(self.message)


class InvalidAnswersError(Exception):
    """Raised when answers are malformed or reference unknown requirement types."""

    def __init__(self, details: list[str]) -> None:
        self.details = details
        self.message = f"Invalid answers: {'; '.join(details)}"
        super().__init__(self.message)


@dataclass
class FailedRequirement:
    """A requirement the adopter did not meet."""

    requirement_type: str
    message: str
    is_mandatory: bool


@dataclass
class SuggestedAnimal:
    """An animal that matches the adopter's profile."""

    id: UUID
    name: str
    species: str
    photo_url: str | None
    match_score: int


@dataclass
class PreQualificationResult:
    """Result of pre-qualification scoring."""

    qualified: bool
    score: int
    failed_requirements: list[FailedRequirement] = field(default_factory=list)
    suggested_animals: list[SuggestedAnimal] = field(default_factory=list)
    estimated_wait_time: str = ""


def _check_yard_answer(requirement_value: dict, answer: dict) -> bool:
    """Check if adopter's yard answer meets the requirement."""
    required_yard = requirement_value.get("yard")
    adopter_yard = answer.get("yard")
    if required_yard == "required":
        return adopter_yard == "yes"
    if required_yard == "preferred":
        # Preferred is always met (just gives bonus points)
        return True
    # not_needed: always passes
    return True


def _check_no_children_under(requirement_value: dict, answer: dict) -> bool:
    """Check if adopter has children under the minimum age."""
    min_age = requirement_value.get("age", 0)
    youngest_child_age = answer.get("youngest_child_age")
    if youngest_child_age is None:
        # No children: passes
        return True
    if not isinstance(youngest_child_age, int):
        return False
    return youngest_child_age >= min_age


def _check_experience_required(requirement_value: dict, answer: dict) -> bool:
    """Check if adopter has required experience level."""
    required_level = requirement_value.get("level")
    adopter_level = answer.get("level")
    experience_hierarchy = {"none": 0, "some": 1, "experienced": 2}
    required_rank = experience_hierarchy.get(required_level, 0)
    adopter_rank = experience_hierarchy.get(adopter_level, 0)
    return adopter_rank >= required_rank


def _check_home_type(requirement_value: dict, answer: dict) -> bool:
    """Check if adopter's home type is in the allowed list."""
    allowed_types = requirement_value.get("types", [])
    adopter_home = answer.get("home_type")
    return adopter_home in allowed_types


def _check_max_hours_alone(requirement_value: dict, answer: dict) -> bool:
    """Check if adopter's hours-alone is within limit."""
    max_hours = requirement_value.get("hours", 24)
    adopter_hours = answer.get("hours_alone")
    if not isinstance(adopter_hours, int):
        return False
    return adopter_hours <= max_hours


def _check_other_pets_ok(requirement_value: dict, answer: dict) -> bool:
    """Check if adopter's existing pets are compatible."""
    allowed_pets = set(requirement_value.get("pets", []))
    adopter_pets = answer.get("existing_pets", [])
    if not adopter_pets:
        # No other pets: always compatible
        return True
    return set(adopter_pets).issubset(allowed_pets)


def _check_housing_status(requirement_value: dict, answer: dict) -> bool:
    """Check if adopter's housing status matches."""
    required_status = requirement_value.get("status")
    adopter_status = answer.get("housing_status")
    return adopter_status == required_status


def _check_income_requirement(requirement_value: dict, answer: dict) -> bool:
    """Check if adopter meets income requirement."""
    min_monthly = requirement_value.get("monthly", 0)
    adopter_monthly = answer.get("monthly_income")
    if not isinstance(adopter_monthly, int):
        return False
    return adopter_monthly >= min_monthly


# Mapping of requirement type to checker function
_REQUIREMENT_CHECKERS: dict[str, typing.Callable[..., bool]] = {
    RequirementType.YARD_REQUIRED: _check_yard_answer,
    RequirementType.NO_CHILDREN_UNDER: _check_no_children_under,
    RequirementType.EXPERIENCE_REQUIRED: _check_experience_required,
    RequirementType.HOME_TYPE: _check_home_type,
    RequirementType.MAX_HOURS_ALONE: _check_max_hours_alone,
    RequirementType.OTHER_PETS_OK: _check_other_pets_ok,
    RequirementType.HOUSING_STATUS: _check_housing_status,
    RequirementType.INCOME_REQUIREMENT: _check_income_requirement,
}


def _generate_failure_message(requirement_type: str, requirement_value: dict, answer: dict) -> str:
    """Generate human-readable failure message for a failed requirement."""
    description = REQUIREMENT_DESCRIPTIONS.get(requirement_type, requirement_type)

    match requirement_type:
        case RequirementType.YARD_REQUIRED:
            return f"{description}: a yard is required but your answer was '{answer.get('yard', 'not provided')}'"
        case RequirementType.NO_CHILDREN_UNDER:
            min_age = requirement_value.get("age", 0)
            child_age = answer.get("youngest_child_age", "not provided")
            return f"{description}: no children under {min_age} years, but youngest child is {child_age}"
        case RequirementType.EXPERIENCE_REQUIRED:
            required = requirement_value.get("level", "unknown")
            provided = answer.get("level", "not provided")
            return f"{description}: '{required}' experience required but you indicated '{provided}'"
        case RequirementType.HOME_TYPE:
            allowed = requirement_value.get("types", [])
            provided = answer.get("home_type", "not provided")
            return f"{description}: allowed home types are {', '.join(allowed)} but yours is '{provided}'"
        case RequirementType.MAX_HOURS_ALONE:
            max_h = requirement_value.get("hours", 0)
            provided = answer.get("hours_alone", "not provided")
            return f"{description}: maximum {max_h} hours alone but you indicated {provided} hours"
        case RequirementType.OTHER_PETS_OK:
            allowed = requirement_value.get("pets", [])
            provided = answer.get("existing_pets", [])
            return f"{description}: compatible pets are {', '.join(allowed)} but you have {', '.join(provided)}"
        case RequirementType.HOUSING_STATUS:
            required = requirement_value.get("status", "unknown")
            provided = answer.get("housing_status", "not provided")
            return f"{description}: '{required}' housing required but yours is '{provided}'"
        case RequirementType.INCOME_REQUIREMENT:
            minimum = requirement_value.get("monthly", 0)
            provided = answer.get("monthly_income", "not provided")
            return (
                f"{description}: minimum monthly income {minimum} required but yours is {provided}"
            )
        case _:
            return f"Requirement '{requirement_type}' not met"


def score_answers(
    requirements: list[AdoptionRequirement],
    answers: dict[str, dict],
) -> PreQualificationResult:
    """Score adopter answers against a list of requirements.

    Args:
        requirements: merged list of requirements for the animal.
        answers: dict keyed by requirement_type, values are answer dicts.

    Returns:
        PreQualificationResult with qualification status, score, and failures.
    """
    if not requirements:
        return PreQualificationResult(qualified=True, score=MAX_SCORE)

    failed: list[FailedRequirement] = []
    met_count = 0
    all_mandatory_met = True

    for req in requirements:
        checker = _REQUIREMENT_CHECKERS.get(req.requirement_type)
        if checker is None:
            # Unknown requirement type — skip
            continue

        answer = answers.get(req.requirement_type, {})
        is_met = checker(req.value, answer)

        if is_met:
            met_count += 1
        else:
            failure_msg = _generate_failure_message(req.requirement_type, req.value, answer)
            failed.append(
                FailedRequirement(
                    requirement_type=req.requirement_type,
                    message=failure_msg,
                    is_mandatory=req.is_mandatory,
                )
            )
            if req.is_mandatory:
                all_mandatory_met = False

    total = len(requirements)
    raw_score = int((met_count / total) * MAX_SCORE) if total > 0 else MAX_SCORE
    bounded_score = max(MIN_SCORE, min(MAX_SCORE, raw_score))

    return PreQualificationResult(
        qualified=all_mandatory_met,
        score=bounded_score,
        failed_requirements=failed,
    )


async def _verify_animal_available(db: AsyncSession, animal_id: UUID) -> Animal:
    """Verify animal exists and is available for adoption."""
    animal = await db.get(Animal, animal_id)
    if animal is None or animal.status != AnimalStatus.AVAILABLE:
        raise AnimalNotFoundError(animal_id)
    return animal


async def _estimate_wait_time(db: AsyncSession, animal_id: UUID) -> str:
    """Estimate wait time based on pending adoption requests in queue."""
    count_query = (
        select(func.count())
        .select_from(AdoptionRequest)
        .where(
            AdoptionRequest.animal_id == animal_id,
            AdoptionRequest.status == AdoptionRequestStatus.PENDING,
        )
    )
    result = await db.execute(count_query)
    pending_count = result.scalar_one()

    total_weeks = BASE_WAIT_WEEKS + (pending_count * WEEKS_PER_PENDING_REQUEST)
    low = total_weeks
    high = total_weeks + 1

    if low <= 1:
        return "1-2 weeks"
    return f"{low}-{high} weeks"


async def _find_suggested_animals(
    db: AsyncSession,
    answers: dict[str, dict],
    exclude_animal_id: UUID | None = None,
) -> list[SuggestedAnimal]:
    """Find available animals that match the adopter's profile.

    Basic matching: fetch available animals, score each against adopter answers.
    Full smart matching deferred to RAP-522.
    """
    query = select(Animal).where(Animal.status == AnimalStatus.AVAILABLE)
    if exclude_animal_id is not None:
        query = query.where(Animal.id != exclude_animal_id)
    query = query.limit(50)  # Fetch a batch to score

    result = await db.execute(query)
    candidates = list(result.scalars().all())

    if not candidates:
        return []

    scored: list[tuple[Animal, int]] = []
    for animal in candidates:
        # Fetch requirements for this animal
        animal_reqs = await get_animal_requirements(db, animal.id)
        if not animal_reqs:
            # No requirements = easy match
            scored.append((animal, MAX_SCORE))
            continue

        prequal = score_answers(animal_reqs, answers)
        if prequal.qualified:
            scored.append((animal, prequal.score))

    # Sort by score descending, take top N
    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:MAX_SUGGESTED_ANIMALS]

    return [
        SuggestedAnimal(
            id=animal.id,
            name=animal.name,
            species=animal.species,
            photo_url=animal.primary_photo_url,
            match_score=score,
        )
        for animal, score in top
    ]


async def pre_qualify_adopter(
    db: AsyncSession,
    animal_id: UUID,
    answers: dict[str, dict],
) -> PreQualificationResult:
    """Run full pre-qualification for an adopter against an animal.

    1. Verify animal exists and is available.
    2. Fetch merged requirements for the animal.
    3. Score answers against requirements.
    4. Find suggested alternative animals.
    5. Estimate wait time.
    """
    await _verify_animal_available(db, animal_id)

    requirements = await get_animal_requirements(db, animal_id)

    result = score_answers(requirements, answers)

    # Add suggested animals (alternatives that also match)
    result.suggested_animals = await _find_suggested_animals(
        db, answers, exclude_animal_id=animal_id
    )

    # Add wait time estimate
    result.estimated_wait_time = await _estimate_wait_time(db, animal_id)

    logger.info(
        "Pre-qualification completed: animal=%s qualified=%s score=%d",
        animal_id,
        result.qualified,
        result.score,
    )

    return result
