"""Foster placement matching service (RAP-191).

Scores approved foster families against animals that need fostering, and
scores available animals against a foster family's profile.  Staff use the
resulting ranked lists to make placement decisions quickly.

Scoring model (foster family → animal):
    +20  Animal species matches preferred_animal_types (or family accepts any)
    +15  Home has outdoor space  (only awarded if the animal's species is 'dog'
         or size is 'large' / 'extra_large')
    +10  Family has no other pets  (awarded when animal records require isolation
         or family has no other pets)
    +20  Foster family has remaining capacity
    + 5  Family has prior experience (experience_description is not empty)
    ──────────────────────────────────────────────────────────────────────────
    max  70 raw points, normalised to 0-100

A foster family with zero remaining capacity is scored 0 and excluded from
the ranked results.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.animal import Animal, AnimalSize, AnimalSpecies, AnimalStatus
from src.db.models.foster_placement import FosterPlacement
from src.db.models.foster_profile import AnimalTypePreference, FosterProfile, FosterStatus

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scoring constants
# ---------------------------------------------------------------------------

SPECIES_MATCH_BONUS = 20
OUTDOOR_SPACE_BONUS = 15
NO_OTHER_PETS_BONUS = 10
CAPACITY_AVAILABLE_BONUS = 20
EXPERIENCE_BONUS = 5
RAW_MAX_SCORE = (
    SPECIES_MATCH_BONUS
    + OUTDOOR_SPACE_BONUS
    + NO_OTHER_PETS_BONUS
    + CAPACITY_AVAILABLE_BONUS
    + EXPERIENCE_BONUS
)

# Animal species → preferred_animal_types values that are compatible
_SPECIES_TO_PREFERENCE: dict[str, str] = {
    AnimalSpecies.DOG: AnimalTypePreference.DOGS,
    AnimalSpecies.CAT: AnimalTypePreference.CATS,
    AnimalSpecies.OTHER: AnimalTypePreference.SMALL_ANIMALS,
}

# Large / extra-large animals benefit most from outdoor space
_LARGE_SIZES: frozenset[str] = frozenset({AnimalSize.LARGE, AnimalSize.EXTRA_LARGE})

# Statuses that indicate an animal is available for fostering
FOSTERABLE_STATUSES: frozenset[str] = frozenset(
    {
        AnimalStatus.INTAKE,
        AnimalStatus.QUARANTINE,
        AnimalStatus.AVAILABLE,
        AnimalStatus.UNDER_TREATMENT,
    }
)

DEFAULT_LIMIT = 10
MAX_LIMIT = 50


# ---------------------------------------------------------------------------
# Public data classes
# ---------------------------------------------------------------------------


@dataclass
class FosterMatch:
    """A foster family with its compatibility score and explanations."""

    foster_profile_id: UUID
    user_id: UUID
    home_type: str
    has_outdoor_space: bool
    has_other_pets: bool
    max_animals: int
    current_placements: int
    preferred_animal_types: list[str]
    match_score: int
    why_match: list[str] = field(default_factory=list)
    why_not: list[str] = field(default_factory=list)


@dataclass
class AnimalFosterMatch:
    """An animal with its compatibility score against a foster family."""

    animal_id: UUID
    name: str
    species: str
    size: str | None
    match_score: int
    why_match: list[str] = field(default_factory=list)
    why_not: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _normalise_score(raw: int) -> int:
    """Normalise a raw score to 0-100."""
    if RAW_MAX_SCORE == 0:
        return 0
    return min(100, max(0, round(raw * 100 / RAW_MAX_SCORE)))


def _score_foster_for_animal(
    profile: FosterProfile,
    animal: Animal,
    current_placements: int,
) -> FosterMatch:
    """Compute a match score for a single foster family against an animal.

    Returns a FosterMatch with the normalised score and human-readable reasons.
    A family that has no remaining capacity always receives score 0.
    """
    raw_score = 0
    why_match: list[str] = []
    why_not: list[str] = []

    # --- Capacity check (gate) -------------------------------------------
    remaining = profile.max_animals - current_placements
    if remaining <= 0:
        return FosterMatch(
            foster_profile_id=profile.id,
            user_id=profile.user_id,
            home_type=profile.home_type,
            has_outdoor_space=profile.has_outdoor_space,
            has_other_pets=profile.has_other_pets,
            max_animals=profile.max_animals,
            current_placements=current_placements,
            preferred_animal_types=profile.preferred_animal_types or [],
            match_score=0,
            why_not=["At maximum capacity — cannot accept more animals"],
        )

    raw_score += CAPACITY_AVAILABLE_BONUS
    why_match.append(f"Has capacity for {remaining} more animal(s)")

    # --- Species preference -----------------------------------------------
    preferred: list[str] = profile.preferred_animal_types or []
    species_pref = _SPECIES_TO_PREFERENCE.get(animal.species)
    if AnimalTypePreference.ANY in preferred:
        raw_score += SPECIES_MATCH_BONUS
        why_match.append("Accepts any animal type")
    elif species_pref and species_pref in preferred:
        raw_score += SPECIES_MATCH_BONUS
        why_match.append(f"Prefers {animal.species}s")
    else:
        why_not.append(f"Does not list {animal.species}s as preferred — may still accept")

    # --- Outdoor space (bonus for dogs and large animals) ------------------
    needs_outdoor = animal.species == AnimalSpecies.DOG or (
        animal.size is not None and animal.size in _LARGE_SIZES
    )
    if profile.has_outdoor_space:
        if needs_outdoor:
            raw_score += OUTDOOR_SPACE_BONUS
            why_match.append("Has outdoor space — ideal for this animal")
        else:
            # Still add partial bonus — outdoor space is always a plus
            raw_score += OUTDOOR_SPACE_BONUS // 2
            why_match.append("Has outdoor space")
    elif needs_outdoor:
        why_not.append("No outdoor space — less ideal for dogs / large animals")

    # --- Other pets -------------------------------------------------------
    if not profile.has_other_pets:
        raw_score += NO_OTHER_PETS_BONUS
        why_match.append("No other pets — lower risk of conflict")
    else:
        why_not.append("Has other pets — may need gradual introduction")

    # --- Experience bonus -------------------------------------------------
    if profile.experience_description and profile.experience_description.strip():
        raw_score += EXPERIENCE_BONUS
        why_match.append("Has prior foster / pet experience")

    return FosterMatch(
        foster_profile_id=profile.id,
        user_id=profile.user_id,
        home_type=profile.home_type,
        has_outdoor_space=profile.has_outdoor_space,
        has_other_pets=profile.has_other_pets,
        max_animals=profile.max_animals,
        current_placements=current_placements,
        preferred_animal_types=preferred,
        match_score=_normalise_score(raw_score),
        why_match=why_match,
        why_not=why_not,
    )


def _score_animal_for_foster(
    profile: FosterProfile,
    animal: Animal,
    current_placements: int,
) -> AnimalFosterMatch:
    """Score an animal against a foster family's profile.

    Reuses the same scoring logic; the perspective is reversed for readability.
    Returns score 0 when the family is at capacity.
    """
    foster_match = _score_foster_for_animal(profile, animal, current_placements)
    return AnimalFosterMatch(
        animal_id=animal.id,
        name=animal.name,
        species=animal.species,
        size=animal.size,
        match_score=foster_match.match_score,
        why_match=foster_match.why_match,
        why_not=foster_match.why_not,
    )


# ---------------------------------------------------------------------------
# Async DB helpers
# ---------------------------------------------------------------------------


async def _get_placement_counts(
    db: AsyncSession,
    profile_ids: list[UUID],
) -> dict[UUID, int]:
    """Return {foster_profile_id: active_placement_count} for a list of profiles."""
    if not profile_ids:
        return {}
    stmt = (
        select(
            FosterPlacement.foster_profile_id,
            func.count().label("cnt"),
        )
        .where(FosterPlacement.foster_profile_id.in_(profile_ids))
        .where(FosterPlacement.ended_at.is_(None))
        .group_by(FosterPlacement.foster_profile_id)
    )
    result = await db.execute(stmt)
    return {row.foster_profile_id: row.cnt for row in result}


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


async def find_foster_matches_for_animal(
    db: AsyncSession,
    animal_id: UUID,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
) -> dict:
    """Find approved foster families ranked by compatibility with a given animal.

    Returns:
        {
            "animal_id": str,
            "animal_name": str,
            "matches": [...],
            "total_eligible": int,
        }

    Families with zero capacity are excluded from results.
    """
    if limit > MAX_LIMIT:
        limit = MAX_LIMIT

    animal_result = await db.execute(select(Animal).where(Animal.id == animal_id))
    animal = animal_result.scalar_one_or_none()
    if animal is None:
        return {
            "animal_id": str(animal_id),
            "animal_name": None,
            "matches": [],
            "total_eligible": 0,
        }

    profiles_result = await db.execute(
        select(FosterProfile).where(FosterProfile.status == FosterStatus.APPROVED)
    )
    profiles: list[FosterProfile] = list(profiles_result.scalars().all())

    if not profiles:
        return {
            "animal_id": str(animal_id),
            "animal_name": animal.name,
            "matches": [],
            "total_eligible": 0,
        }

    counts = await _get_placement_counts(db, [p.id for p in profiles])

    scored: list[FosterMatch] = []
    for profile in profiles:
        current = counts.get(profile.id, 0)
        match = _score_foster_for_animal(profile, animal, current)
        if match.match_score > 0:
            scored.append(match)

    scored.sort(key=lambda m: (-m.match_score, str(m.foster_profile_id)))
    total_eligible = len(scored)
    paginated = scored[offset : offset + limit]

    logger.info(
        "Foster matching completed for animal",
        extra={
            "animal_id": str(animal_id),
            "total_eligible_families": total_eligible,
            "returned": len(paginated),
        },
    )

    return {
        "animal_id": str(animal_id),
        "animal_name": animal.name,
        "matches": [
            {
                "foster_profile_id": str(m.foster_profile_id),
                "user_id": str(m.user_id),
                "home_type": m.home_type,
                "has_outdoor_space": m.has_outdoor_space,
                "has_other_pets": m.has_other_pets,
                "max_animals": m.max_animals,
                "current_placements": m.current_placements,
                "remaining_capacity": m.max_animals - m.current_placements,
                "preferred_animal_types": m.preferred_animal_types,
                "match_score": m.match_score,
                "why_match": m.why_match,
                "why_not": m.why_not,
            }
            for m in paginated
        ],
        "total_eligible": total_eligible,
    }


async def find_animal_matches_for_foster(
    db: AsyncSession,
    foster_profile_id: UUID,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
) -> dict:
    """Find fosterable animals ranked by compatibility with a given foster family.

    Returns:
        {
            "foster_profile_id": str,
            "matches": [...],
            "total_eligible": int,
        }

    Returns empty list if the family is at capacity or not approved.
    """
    if limit > MAX_LIMIT:
        limit = MAX_LIMIT

    profile_result = await db.execute(
        select(FosterProfile).where(FosterProfile.id == foster_profile_id)
    )
    profile = profile_result.scalar_one_or_none()
    if profile is None or profile.status != FosterStatus.APPROVED:
        return {
            "foster_profile_id": str(foster_profile_id),
            "matches": [],
            "total_eligible": 0,
        }

    counts = await _get_placement_counts(db, [profile.id])
    current_placements = counts.get(profile.id, 0)

    if current_placements >= profile.max_animals:
        return {
            "foster_profile_id": str(foster_profile_id),
            "matches": [],
            "total_eligible": 0,
            "note": "Family is at maximum capacity",
        }

    animals_result = await db.execute(
        select(Animal).where(Animal.status.in_(list(FOSTERABLE_STATUSES)))
    )
    animals: list[Animal] = list(animals_result.scalars().all())

    scored: list[AnimalFosterMatch] = []
    for animal in animals:
        match = _score_animal_for_foster(profile, animal, current_placements)
        if match.match_score > 0:
            scored.append(match)

    scored.sort(key=lambda m: (-m.match_score, str(m.animal_id)))
    total_eligible = len(scored)
    paginated = scored[offset : offset + limit]

    logger.info(
        "Animal matching completed for foster family",
        extra={
            "foster_profile_id": str(foster_profile_id),
            "total_eligible_animals": total_eligible,
            "returned": len(paginated),
        },
    )

    return {
        "foster_profile_id": str(foster_profile_id),
        "matches": [
            {
                "animal_id": str(m.animal_id),
                "name": m.name,
                "species": m.species,
                "size": m.size,
                "match_score": m.match_score,
                "why_match": m.why_match,
                "why_not": m.why_not,
            }
            for m in paginated
        ],
        "total_eligible": total_eligible,
    }
