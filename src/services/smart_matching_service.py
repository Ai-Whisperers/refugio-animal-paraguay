"""Smart matching service for ranking animals against adopter profiles.

Scores available animals against adopter answers to adoption requirements,
returning a ranked list of best-fit animals with match explanations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.adoption_requirement import (
    RequirementType,
)
from src.db.models.animal import Animal, AnimalStatus
from src.services.adoption_requirement_service import get_animal_requirements
from src.services.pre_qualification_service import _REQUIREMENT_CHECKERS

logger = logging.getLogger(__name__)

# Scoring constants
MANDATORY_MET_BONUS = 5
PREFERRED_MET_BONUS = 10
SPECIES_PREFERENCE_BONUS = 10
SIZE_PREFERENCE_BONUS = 5
EXPERIENCE_BONUS = 10
NO_REQUIREMENTS_SCORE = 50
MAX_MATCH_SCORE = 100
MIN_MATCH_SCORE = 0
DEFAULT_LIMIT = 10
MAX_LIMIT = 50

# Cache TTL (seconds)
MATCH_CACHE_TTL_SECONDS = 3600


@dataclass
class MatchReason:
    """A human-readable reason for why an animal matches an adopter."""

    reason: str
    bonus_points: int = 0


@dataclass
class AnimalMatch:
    """An animal with its match score and explanations."""

    animal_id: UUID
    name: str
    species: str
    breed: str | None
    birth_date: date | None
    photo_url: str | None
    match_score: int
    why_match: list[str] = field(default_factory=list)


def _generate_match_reason(requirement_type: str, met: bool) -> str | None:
    """Generate a human-readable match reason for a met requirement."""
    if not met:
        return None

    reason_map = {
        RequirementType.YARD_REQUIRED: "Has a yard suitable for this animal",
        RequirementType.NO_CHILDREN_UNDER: "Household meets child age requirements",
        RequirementType.EXPERIENCE_REQUIRED: "Has required pet experience",
        RequirementType.HOME_TYPE: "Home type is compatible",
        RequirementType.MAX_HOURS_ALONE: "Work schedule is compatible",
        RequirementType.OTHER_PETS_OK: "Other pets situation is compatible",
        RequirementType.HOUSING_STATUS: "Housing ownership is suitable",
        RequirementType.INCOME_REQUIREMENT: "Meets income requirements",
    }
    return reason_map.get(requirement_type, f"Meets {requirement_type} requirement")


async def _score_animal(
    db: AsyncSession,
    animal: Animal,
    answers: dict[str, dict],
) -> AnimalMatch:
    """Score a single animal against adopter answers.

    Returns an AnimalMatch with computed match_score and why_match reasons.
    """
    requirements = await get_animal_requirements(db, animal.id)

    met_count = 0
    total_count = len(requirements)
    bonus_points = 0
    why_match: list[str] = []

    if not requirements:
        why_match.append("No specific requirements — compatible with most adopters")

    for req in requirements:
        answer = answers.get(req.requirement_type)
        if answer is None:
            # Missing answer — treat as not met
            continue

        checker = _REQUIREMENT_CHECKERS.get(req.requirement_type)
        if checker is None:
            # Unknown requirement type — skip
            continue

        met = checker(req.value, answer)
        if met:
            met_count += 1
            # Apply bonuses based on priority
            if req.priority == "mandatory":
                bonus_points += MANDATORY_MET_BONUS
            elif req.priority == "preferred":
                bonus_points += PREFERRED_MET_BONUS

            reason = _generate_match_reason(req.requirement_type, met)
            if reason:
                why_match.append(reason)

    # Base score: percentage of requirements met
    base_score = int((met_count / total_count) * 100) if total_count > 0 else NO_REQUIREMENTS_SCORE

    # Apply species preference bonus
    species_pref = answers.get("species_preference", {})
    if species_pref and species_pref.get("value") == animal.species:
        bonus_points += SPECIES_PREFERENCE_BONUS
        why_match.append(f"Matches your {animal.species} preference")

    # Apply size preference bonus
    size_pref = answers.get("size_preference", {})
    animal_size = animal.size
    if size_pref and animal_size and size_pref.get("value") == animal_size:
        bonus_points += SIZE_PREFERENCE_BONUS
        why_match.append("Size matches your preference")

    # Final score: base + bonuses, capped
    final_score = min(MAX_MATCH_SCORE, max(MIN_MATCH_SCORE, base_score + bonus_points))

    return AnimalMatch(
        animal_id=animal.id,
        name=animal.name,
        species=animal.species,
        breed=animal.breed,
        birth_date=animal.birth_date,
        photo_url=animal.primary_photo_url,
        match_score=final_score,
        why_match=why_match,
    )


async def find_matches(
    db: AsyncSession,
    answers: dict[str, dict],
    species: str | None = None,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
) -> dict:
    """Find and rank available animals against adopter answers.

    Returns a dict with:
    - animals: list of AnimalMatch dicts, sorted by match_score DESC then animal_id ASC
    - total_count: total number of available animals matched
    """
    # Build base query for available animals
    stmt = select(Animal).where(Animal.status == AnimalStatus.AVAILABLE)

    if species is not None:
        stmt = stmt.where(Animal.species == species)

    result = await db.execute(stmt)
    animals = list(result.scalars().all())

    # Score each animal
    matches: list[AnimalMatch] = []
    for animal in animals:
        match = await _score_animal(db, animal, answers)
        matches.append(match)

    # Sort: match_score DESC, then animal_id ASC (deterministic tie-breaking)
    matches.sort(key=lambda m: (-m.match_score, str(m.animal_id)))

    total_count = len(matches)

    # Apply pagination
    paginated = matches[offset : offset + limit]

    return {
        "animals": [
            {
                "id": str(m.animal_id),
                "name": m.name,
                "species": m.species,
                "breed": m.breed,
                "birth_date": m.birth_date.isoformat() if m.birth_date else None,
                "photo_url": m.photo_url,
                "match_score": m.match_score,
                "why_match": m.why_match,
            }
            for m in paginated
        ],
        "total_count": total_count,
    }
