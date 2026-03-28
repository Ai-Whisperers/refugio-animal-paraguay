"""Service for managing configurable adoption requirements.

Handles CRUD for global and animal-specific requirements, merging
logic (animal-specific overrides global of same type), and
pre-qualification question generation.
"""

import logging
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.adoption_requirement import (
    REQUIREMENT_DESCRIPTIONS,
    AdoptionRequirement,
    RequirementType,
)

logger = logging.getLogger(__name__)

# Valid value schemas per requirement type (for validation)
_VALID_YARD_VALUES = {"required", "preferred", "not_needed"}
_VALID_EXPERIENCE_LEVELS = {"none", "some", "experienced"}
_VALID_HOME_TYPES = {"apartment", "house", "farm"}
_VALID_PET_TYPES = {"cats", "dogs", "other"}
_VALID_HOUSING_STATUSES = {"owned", "rented"}


class RequirementNotFoundError(Exception):
    """Raised when an adoption requirement is not found."""

    def __init__(self, requirement_id: UUID) -> None:
        self.requirement_id = requirement_id
        self.message = f"Adoption requirement {requirement_id} not found."
        super().__init__(self.message)


class InvalidRequirementValueError(Exception):
    """Raised when a requirement value doesn't match expected schema."""

    def __init__(self, requirement_type: str, detail: str) -> None:
        self.requirement_type = requirement_type
        self.detail = detail
        self.message = f"Invalid value for {requirement_type}: {detail}"
        super().__init__(self.message)


def validate_requirement_value(requirement_type: str, value: dict) -> None:
    """Validate that the value JSON matches the schema for the given type.

    Raises InvalidRequirementValueError if validation fails.
    """
    if not isinstance(value, dict):
        raise InvalidRequirementValueError(requirement_type, "Value must be a JSON object")

    match requirement_type:
        case RequirementType.YARD_REQUIRED:
            yard = value.get("yard")
            if yard not in _VALID_YARD_VALUES:
                raise InvalidRequirementValueError(
                    requirement_type,
                    f"'yard' must be one of: {', '.join(sorted(_VALID_YARD_VALUES))}",
                )

        case RequirementType.NO_CHILDREN_UNDER:
            age = value.get("age")
            if not isinstance(age, int) or age < 0 or age > 18:
                raise InvalidRequirementValueError(
                    requirement_type, "'age' must be an integer between 0 and 18"
                )

        case RequirementType.EXPERIENCE_REQUIRED:
            level = value.get("level")
            if level not in _VALID_EXPERIENCE_LEVELS:
                raise InvalidRequirementValueError(
                    requirement_type,
                    f"'level' must be one of: {', '.join(sorted(_VALID_EXPERIENCE_LEVELS))}",
                )

        case RequirementType.HOME_TYPE:
            types = value.get("types")
            if not isinstance(types, list) or not types:
                raise InvalidRequirementValueError(
                    requirement_type, "'types' must be a non-empty list"
                )
            invalid = set(types) - _VALID_HOME_TYPES
            if invalid:
                raise InvalidRequirementValueError(
                    requirement_type,
                    f"Invalid home types: {', '.join(sorted(invalid))}. "
                    f"Valid: {', '.join(sorted(_VALID_HOME_TYPES))}",
                )

        case RequirementType.MAX_HOURS_ALONE:
            hours = value.get("hours")
            if not isinstance(hours, int) or hours < 0 or hours > 24:
                raise InvalidRequirementValueError(
                    requirement_type, "'hours' must be an integer between 0 and 24"
                )

        case RequirementType.OTHER_PETS_OK:
            pets = value.get("pets")
            if not isinstance(pets, list) or not pets:
                raise InvalidRequirementValueError(
                    requirement_type, "'pets' must be a non-empty list"
                )
            invalid = set(pets) - _VALID_PET_TYPES
            if invalid:
                raise InvalidRequirementValueError(
                    requirement_type,
                    f"Invalid pet types: {', '.join(sorted(invalid))}. "
                    f"Valid: {', '.join(sorted(_VALID_PET_TYPES))}",
                )

        case RequirementType.HOUSING_STATUS:
            status = value.get("status")
            if status not in _VALID_HOUSING_STATUSES:
                raise InvalidRequirementValueError(
                    requirement_type,
                    f"'status' must be one of: {', '.join(sorted(_VALID_HOUSING_STATUSES))}",
                )

        case RequirementType.INCOME_REQUIREMENT:
            monthly = value.get("monthly")
            if not isinstance(monthly, int) or monthly < 0:
                raise InvalidRequirementValueError(
                    requirement_type, "'monthly' must be a non-negative integer (EUR cents)"
                )

        case _:
            raise InvalidRequirementValueError(
                requirement_type, f"Unknown requirement type: {requirement_type}"
            )


async def create_requirement(
    db: AsyncSession,
    *,
    requirement_type: str,
    value: dict,
    is_mandatory: bool = True,
    animal_id: UUID | None = None,
) -> AdoptionRequirement:
    """Create a new adoption requirement (global or animal-specific)."""
    validate_requirement_value(requirement_type, value)

    requirement = AdoptionRequirement(
        animal_id=animal_id,
        requirement_type=requirement_type,
        value=value,
        is_mandatory=is_mandatory,
    )
    db.add(requirement)
    await db.flush()
    await db.refresh(requirement)

    scope = f"animal {animal_id}" if animal_id else "global"
    logger.info("Created %s adoption requirement: %s (%s)", scope, requirement.id, requirement_type)
    return requirement


async def get_requirement(db: AsyncSession, requirement_id: UUID) -> AdoptionRequirement:
    """Fetch a requirement by ID. Raises RequirementNotFoundError if missing."""
    requirement = await db.get(AdoptionRequirement, requirement_id)
    if requirement is None or not requirement.active:
        raise RequirementNotFoundError(requirement_id)
    return requirement


async def update_requirement(
    db: AsyncSession,
    requirement_id: UUID,
    *,
    value: dict | None = None,
    is_mandatory: bool | None = None,
) -> AdoptionRequirement:
    """Update an existing requirement's value or mandatory flag."""
    requirement = await get_requirement(db, requirement_id)

    if value is not None:
        validate_requirement_value(requirement.requirement_type, value)
        requirement.value = value

    if is_mandatory is not None:
        requirement.is_mandatory = is_mandatory

    await db.flush()
    await db.refresh(requirement)

    logger.info("Updated adoption requirement %s", requirement_id)
    return requirement


async def soft_delete_requirement(db: AsyncSession, requirement_id: UUID) -> None:
    """Soft-delete a requirement by setting active=false."""
    await get_requirement(db, requirement_id)

    stmt = (
        update(AdoptionRequirement)
        .where(AdoptionRequirement.id == requirement_id)
        .values(active=False)
    )
    await db.execute(stmt)
    await db.flush()

    logger.info("Soft-deleted adoption requirement %s", requirement_id)


async def get_animal_requirements(
    db: AsyncSession,
    animal_id: UUID,
) -> list[AdoptionRequirement]:
    """Get merged requirements for an animal.

    Returns animal-specific requirements merged with global requirements.
    Animal-specific requirements override global requirements of the same type.
    """
    # Fetch global requirements
    global_query = select(AdoptionRequirement).where(
        AdoptionRequirement.animal_id.is_(None),
        AdoptionRequirement.active.is_(True),
    )
    global_result = await db.execute(global_query)
    global_reqs = list(global_result.scalars().all())

    # Fetch animal-specific requirements
    animal_query = select(AdoptionRequirement).where(
        AdoptionRequirement.animal_id == animal_id,
        AdoptionRequirement.active.is_(True),
    )
    animal_result = await db.execute(animal_query)
    animal_reqs = list(animal_result.scalars().all())

    # Merge: animal-specific overrides global of same type
    animal_types = {r.requirement_type for r in animal_reqs}
    merged = list(animal_reqs)
    for global_req in global_reqs:
        if global_req.requirement_type not in animal_types:
            merged.append(global_req)

    return merged


async def get_pre_qualification_questions(
    db: AsyncSession,
    animal_id: UUID,
) -> list[dict]:
    """Generate pre-qualification questions for an animal.

    Returns a list of questions based on the animal's merged requirements,
    with human-readable descriptions.
    """
    requirements = await get_animal_requirements(db, animal_id)

    questions = []
    for req in requirements:
        questions.append(
            {
                "id": str(req.id),
                "requirement_type": req.requirement_type,
                "value": req.value,
                "is_mandatory": req.is_mandatory,
                "animal_id": str(req.animal_id) if req.animal_id else None,
                "human_readable_description": REQUIREMENT_DESCRIPTIONS.get(
                    req.requirement_type, req.requirement_type
                ),
            }
        )

    return questions
