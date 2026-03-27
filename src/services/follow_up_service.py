"""Service layer for post-adoption follow-up scheduling, surveys, and analytics."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.adoption_request import AdoptionRequest
from src.db.models.animal import Animal
from src.db.models.follow_up import (
    FOLLOW_UP_SCHEDULE_DAYS,
    FollowUp,
    FollowUpStatus,
)


async def schedule_follow_ups(
    db: AsyncSession,
    adoption_request_id: UUID,
    completed_at: datetime,
) -> list[FollowUp]:
    """Create follow-up records for a completed adoption.

    Schedules checks at 7, 30, 90, and 365 days post-completion.
    Idempotent: skips creation if follow-ups already exist for this request.
    """
    existing = await db.execute(
        select(func.count())
        .select_from(FollowUp)
        .where(FollowUp.adoption_request_id == adoption_request_id)
    )
    if existing.scalar_one() > 0:
        return []

    follow_ups: list[FollowUp] = []
    for days in FOLLOW_UP_SCHEDULE_DAYS:
        fu = FollowUp(
            adoption_request_id=adoption_request_id,
            scheduled_date=completed_at + timedelta(days=days),
            day_offset=days,
            status=FollowUpStatus.PENDING.value,
        )
        db.add(fu)
        follow_ups.append(fu)

    await db.flush()
    for fu in follow_ups:
        await db.refresh(fu)
    return follow_ups


async def get_follow_ups_for_request(
    db: AsyncSession,
    adoption_request_id: UUID,
) -> list[FollowUp]:
    """Return all follow-ups for an adoption request, ordered by scheduled date."""
    result = await db.execute(
        select(FollowUp)
        .where(FollowUp.adoption_request_id == adoption_request_id)
        .order_by(FollowUp.scheduled_date)
    )
    return list(result.scalars().all())


async def submit_survey(
    db: AsyncSession,
    follow_up_id: UUID,
    welfare_score: int,
    satisfaction_score: int,
    comments: str | None = None,
    photo_url: str | None = None,
    issues_noted: str | None = None,
) -> FollowUp:
    """Record an adopter's welfare survey response."""
    fu = await db.get(FollowUp, follow_up_id)
    if fu is None:
        msg = f"Follow-up {follow_up_id} not found"
        raise ValueError(msg)

    fu.welfare_score = welfare_score
    fu.satisfaction_score = satisfaction_score
    fu.comments = comments
    fu.photo_url = photo_url
    fu.issues_noted = issues_noted
    fu.survey_completed_at = datetime.now(UTC)
    fu.status = FollowUpStatus.COMPLETED.value
    fu.updated_at = datetime.now(UTC)

    await db.flush()
    await db.refresh(fu)
    return fu


async def record_return(
    db: AsyncSession,
    follow_up_id: UUID,
    return_reason_code: str,
    return_notes: str | None = None,
) -> FollowUp:
    """Record an animal return/rehome on a follow-up."""
    fu = await db.get(FollowUp, follow_up_id)
    if fu is None:
        msg = f"Follow-up {follow_up_id} not found"
        raise ValueError(msg)

    fu.return_date = datetime.now(UTC)
    fu.return_reason_code = return_reason_code
    fu.return_notes = return_notes
    fu.status = FollowUpStatus.COMPLETED.value
    fu.updated_at = datetime.now(UTC)

    await db.flush()
    await db.refresh(fu)
    return fu


async def get_adoption_outcome_stats(
    db: AsyncSession,
) -> dict:
    """Calculate aggregated adoption outcome statistics.

    Returns total completed adoptions, return count, success rate,
    return rate by species, and average survey scores.
    """
    # Total completed adoptions (those that have follow-ups)
    total_q = await db.execute(select(func.count(func.distinct(FollowUp.adoption_request_id))))
    total_completed = total_q.scalar_one()

    # Total returned (follow-ups with return_date set)
    returned_q = await db.execute(
        select(func.count(func.distinct(FollowUp.adoption_request_id))).where(
            FollowUp.return_date.isnot(None)
        )
    )
    total_returned = returned_q.scalar_one()

    success_rate = (
        round((total_completed - total_returned) / total_completed * 100, 1)
        if total_completed > 0
        else 0.0
    )

    # Return rate by species
    # Use CASE to conditionally count returned adoptions (avoids FILTER clause issues)
    species_q = await db.execute(
        select(
            Animal.species,
            func.count(func.distinct(FollowUp.adoption_request_id)).label("total"),
            func.count(
                func.distinct(
                    case(
                        (FollowUp.return_date.isnot(None), FollowUp.adoption_request_id),
                    )
                )
            ).label("returned"),
        )
        .join(
            AdoptionRequest,
            AdoptionRequest.id == FollowUp.adoption_request_id,
        )
        .join(Animal, Animal.id == AdoptionRequest.animal_id)
        .group_by(Animal.species)
    )
    return_rate_by_species: dict[str, float] = {}
    for row in species_q:
        species_total = row.total
        species_returned = row.returned
        rate = round(species_returned / species_total * 100, 1) if species_total > 0 else 0.0
        return_rate_by_species[row.species] = rate

    # Average survey scores
    avg_q = await db.execute(
        select(
            func.avg(FollowUp.welfare_score),
            func.avg(FollowUp.satisfaction_score),
        ).where(FollowUp.survey_completed_at.isnot(None))
    )
    avg_row = avg_q.one()
    avg_welfare = round(float(avg_row[0]), 1) if avg_row[0] is not None else None
    avg_satisfaction = round(float(avg_row[1]), 1) if avg_row[1] is not None else None

    return {
        "total_completed_adoptions": total_completed,
        "total_returned": total_returned,
        "success_rate_pct": success_rate,
        "return_rate_by_species": return_rate_by_species,
        "average_welfare_score": avg_welfare,
        "average_satisfaction_score": avg_satisfaction,
    }
