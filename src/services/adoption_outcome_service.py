"""Service layer for adoption outcome tracking (EPIC-53).

Provides CRUD operations for AdoptionOutcome records plus aggregate
analytics: success rates, return rates, outcome trend analysis, and
satisfaction score summaries.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.adoption_outcome import AdoptionOutcome, AdoptionOutcomeType
from src.db.models.follow_up import FollowUp, FollowUpStatus

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class AdoptionOutcomeNotFoundError(Exception):
    """Raised when an AdoptionOutcome record does not exist."""


class DuplicateAdoptionOutcomeError(Exception):
    """Raised when attempting to create a second outcome for the same adoption."""


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OutcomeStats:
    """Aggregate adoption outcome statistics."""

    total_outcomes: int
    successful: int
    returned: int
    rehomed: int
    deceased: int
    unknown: int
    success_rate_pct: float
    return_rate_pct: float
    avg_welfare_score: float | None
    avg_satisfaction_score: float | None
    avg_followup_completion_rate_pct: float
    generated_at: str


@dataclass(frozen=True)
class OutcomeRecord:
    """Single adoption outcome record."""

    id: UUID
    adoption_request_id: UUID
    outcome_type: str
    outcome_date: datetime | None
    notes: str | None
    avg_welfare_score: float | None
    avg_satisfaction_score: float | None
    total_follow_ups: int
    completed_follow_ups: int
    return_reason_code: str | None
    return_date: datetime | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_rate(numerator: int, denominator: int) -> float:
    """Return percentage (0-100) or 0.0 when denominator is zero."""
    if denominator == 0:
        return 0.0
    return round(numerator / denominator * 100, 2)


async def _sync_follow_up_scores(
    db: AsyncSession, adoption_request_id: UUID
) -> tuple[float | None, float | None, int, int]:
    """Compute aggregated follow-up metrics for an adoption.

    Returns (avg_welfare, avg_satisfaction, total_count, completed_count).
    """
    result = await db.execute(
        select(
            func.count(FollowUp.id).label("total"),
            func.count(FollowUp.id)
            .filter(FollowUp.status == FollowUpStatus.COMPLETED)
            .label("completed"),
            func.avg(FollowUp.welfare_score).label("avg_welfare"),
            func.avg(FollowUp.satisfaction_score).label("avg_satisfaction"),
        ).where(FollowUp.adoption_request_id == adoption_request_id)
    )
    row = result.one()

    avg_welfare = float(row.avg_welfare) if row.avg_welfare is not None else None
    avg_satisfaction = float(row.avg_satisfaction) if row.avg_satisfaction is not None else None
    total = int(row.total)
    completed = int(row.completed)
    return avg_welfare, avg_satisfaction, total, completed


def _record_to_dataclass(outcome: AdoptionOutcome) -> OutcomeRecord:
    return OutcomeRecord(
        id=outcome.id,
        adoption_request_id=outcome.adoption_request_id,
        outcome_type=outcome.outcome_type,
        outcome_date=outcome.outcome_date,
        notes=outcome.notes,
        avg_welfare_score=outcome.avg_welfare_score,
        avg_satisfaction_score=outcome.avg_satisfaction_score,
        total_follow_ups=outcome.total_follow_ups,
        completed_follow_ups=outcome.completed_follow_ups,
        return_reason_code=outcome.return_reason_code,
        return_date=outcome.return_date,
        created_at=outcome.created_at,
        updated_at=outcome.updated_at,
    )


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


async def create_outcome(
    db: AsyncSession,
    adoption_request_id: UUID,
    outcome_type: AdoptionOutcomeType,
    outcome_date: datetime | None = None,
    notes: str | None = None,
    return_reason_code: str | None = None,
    return_date: datetime | None = None,
) -> OutcomeRecord:
    """Create an outcome record for an adoption.

    Automatically syncs aggregated follow-up scores from existing FollowUp rows.

    Raises DuplicateAdoptionOutcomeError if a record for this adoption already exists.
    """
    existing = await db.scalar(
        select(AdoptionOutcome).where(AdoptionOutcome.adoption_request_id == adoption_request_id)
    )
    if existing is not None:
        raise DuplicateAdoptionOutcomeError(
            f"Outcome already exists for adoption {adoption_request_id}"
        )

    avg_welfare, avg_satisfaction, total_fu, completed_fu = await _sync_follow_up_scores(
        db, adoption_request_id
    )

    outcome = AdoptionOutcome(
        adoption_request_id=adoption_request_id,
        outcome_type=outcome_type.value,
        outcome_date=outcome_date or datetime.now(UTC),
        notes=notes,
        avg_welfare_score=avg_welfare,
        avg_satisfaction_score=avg_satisfaction,
        total_follow_ups=total_fu,
        completed_follow_ups=completed_fu,
        return_reason_code=return_reason_code,
        return_date=return_date,
    )
    db.add(outcome)
    await db.flush()
    await db.refresh(outcome)
    logger.info(
        "Adoption outcome created",
        extra={"adoption_request_id": str(adoption_request_id), "outcome_type": outcome_type},
    )
    return _record_to_dataclass(outcome)


async def get_outcome_by_adoption(db: AsyncSession, adoption_request_id: UUID) -> OutcomeRecord:
    """Fetch an outcome record by adoption request ID.

    Raises AdoptionOutcomeNotFoundError if no record exists.
    """
    outcome = await db.scalar(
        select(AdoptionOutcome).where(AdoptionOutcome.adoption_request_id == adoption_request_id)
    )
    if outcome is None:
        raise AdoptionOutcomeNotFoundError(f"No outcome found for adoption {adoption_request_id}")
    return _record_to_dataclass(outcome)


async def get_outcome_by_id(db: AsyncSession, outcome_id: UUID) -> OutcomeRecord:
    """Fetch an outcome record by its own ID.

    Raises AdoptionOutcomeNotFoundError if not found.
    """
    outcome = await db.get(AdoptionOutcome, outcome_id)
    if outcome is None:
        raise AdoptionOutcomeNotFoundError(f"Outcome {outcome_id} not found")
    return _record_to_dataclass(outcome)


async def update_outcome(
    db: AsyncSession,
    adoption_request_id: UUID,
    outcome_type: AdoptionOutcomeType | None = None,
    outcome_date: datetime | None = None,
    notes: str | None = None,
    return_reason_code: str | None = None,
    return_date: datetime | None = None,
    refresh_scores: bool = True,
) -> OutcomeRecord:
    """Update an existing outcome record.

    Pass only the fields that need updating. When refresh_scores=True (default),
    recalculates aggregated follow-up scores from current FollowUp rows.

    Raises AdoptionOutcomeNotFoundError if no record exists.
    """
    outcome = await db.scalar(
        select(AdoptionOutcome).where(AdoptionOutcome.adoption_request_id == adoption_request_id)
    )
    if outcome is None:
        raise AdoptionOutcomeNotFoundError(f"No outcome found for adoption {adoption_request_id}")

    if outcome_type is not None:
        outcome.outcome_type = outcome_type.value
    if outcome_date is not None:
        outcome.outcome_date = outcome_date
    if notes is not None:
        outcome.notes = notes
    if return_reason_code is not None:
        outcome.return_reason_code = return_reason_code
    if return_date is not None:
        outcome.return_date = return_date

    if refresh_scores:
        avg_welfare, avg_satisfaction, total_fu, completed_fu = await _sync_follow_up_scores(
            db, adoption_request_id
        )
        outcome.avg_welfare_score = avg_welfare
        outcome.avg_satisfaction_score = avg_satisfaction
        outcome.total_follow_ups = total_fu
        outcome.completed_follow_ups = completed_fu

    await db.flush()
    await db.refresh(outcome)
    return _record_to_dataclass(outcome)


async def list_outcomes(
    db: AsyncSession,
    outcome_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[OutcomeRecord]:
    """List outcome records with optional filtering by outcome_type."""
    query = select(AdoptionOutcome).order_by(AdoptionOutcome.created_at.desc())
    if outcome_type is not None:
        query = query.where(AdoptionOutcome.outcome_type == outcome_type)
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    return [_record_to_dataclass(row) for row in result.scalars()]


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------


async def get_outcome_stats(db: AsyncSession) -> OutcomeStats:
    """Return aggregate adoption outcome statistics across all records."""
    result = await db.execute(
        select(
            func.count(AdoptionOutcome.id).label("total"),
            func.count(AdoptionOutcome.id)
            .filter(AdoptionOutcome.outcome_type == AdoptionOutcomeType.SUCCESSFUL)
            .label("successful"),
            func.count(AdoptionOutcome.id)
            .filter(AdoptionOutcome.outcome_type == AdoptionOutcomeType.RETURNED)
            .label("returned"),
            func.count(AdoptionOutcome.id)
            .filter(AdoptionOutcome.outcome_type == AdoptionOutcomeType.REHOMED)
            .label("rehomed"),
            func.count(AdoptionOutcome.id)
            .filter(AdoptionOutcome.outcome_type == AdoptionOutcomeType.DECEASED)
            .label("deceased"),
            func.count(AdoptionOutcome.id)
            .filter(AdoptionOutcome.outcome_type == AdoptionOutcomeType.UNKNOWN)
            .label("unknown"),
            func.avg(AdoptionOutcome.avg_welfare_score).label("avg_welfare"),
            func.avg(AdoptionOutcome.avg_satisfaction_score).label("avg_satisfaction"),
            func.avg(
                func.cast(AdoptionOutcome.completed_follow_ups, sa.Float())
                / func.nullif(AdoptionOutcome.total_follow_ups, 0)
                * 100
            ).label("avg_completion_rate"),
        )
    )
    row = result.one()

    total = int(row.total)
    successful = int(row.successful)
    returned = int(row.returned)

    return OutcomeStats(
        total_outcomes=total,
        successful=successful,
        returned=returned,
        rehomed=int(row.rehomed),
        deceased=int(row.deceased),
        unknown=int(row.unknown),
        success_rate_pct=_safe_rate(successful, total),
        return_rate_pct=_safe_rate(returned, total),
        avg_welfare_score=float(row.avg_welfare) if row.avg_welfare is not None else None,
        avg_satisfaction_score=(
            float(row.avg_satisfaction) if row.avg_satisfaction is not None else None
        ),
        avg_followup_completion_rate_pct=(
            round(float(row.avg_completion_rate), 2) if row.avg_completion_rate is not None else 0.0
        ),
        generated_at=datetime.now(UTC).isoformat(),
    )
