"""Service layer for adopter satisfaction survey management (RAP-264, EPIC-53).

Provides survey dispatch tracking, completion analytics, and result retrieval.
Surveys are attached to FollowUp records; the adopter submits via
POST /follow-ups/{id}/survey (existing endpoint, no auth required).

This service adds the *admin-side* view: which surveys are pending, which
are completed, and aggregate satisfaction statistics.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.follow_up import FollowUp, FollowUpStatus

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SURVEY_COMPLETION_THRESHOLD = 1
"""Minimum number of completed surveys required to compute averages."""

# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SurveyStats:
    """Aggregate statistics for survey dispatch and completion."""

    total_scheduled: int
    total_sent: int
    total_completed: int
    send_rate_pct: float
    completion_rate_pct: float
    avg_welfare_score: float | None
    avg_satisfaction_score: float | None


@dataclass(frozen=True)
class PendingSurvey:
    """A follow-up that has not yet had its survey sent."""

    follow_up_id: UUID
    adoption_request_id: UUID
    scheduled_date: datetime
    day_offset: int
    days_overdue: int


@dataclass(frozen=True)
class SurveyResult:
    """A completed survey response."""

    follow_up_id: UUID
    adoption_request_id: UUID
    day_offset: int
    welfare_score: int
    satisfaction_score: int
    survey_completed_at: datetime
    comments: str | None
    issues_noted: str | None


@dataclass(frozen=True)
class MarkSentResult:
    """Result of a bulk mark-as-sent operation."""

    marked_count: int
    already_sent_count: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_avg(total: float, count: int) -> float | None:
    if count < SURVEY_COMPLETION_THRESHOLD:
        return None
    return round(total / count, 1)


def _safe_pct(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator * 100, 2)


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------


async def get_pending_surveys(
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0,
) -> list[PendingSurvey]:
    """Return follow-ups that are due but have not had their survey sent.

    A survey is pending when:
    - status is 'pending' or 'overdue'
    - survey_sent_at is NULL
    - scheduled_date is in the past (already due)

    Results are ordered by scheduled_date ascending (most overdue first).
    """
    now = datetime.now(UTC)
    result = await db.execute(
        select(FollowUp)
        .where(
            FollowUp.survey_sent_at.is_(None),
            FollowUp.survey_completed_at.is_(None),
            FollowUp.scheduled_date <= now,
            FollowUp.status.in_([FollowUpStatus.PENDING.value, FollowUpStatus.OVERDUE.value]),
        )
        .order_by(FollowUp.scheduled_date.asc())
        .limit(limit)
        .offset(offset)
    )
    rows = result.scalars().all()

    pending = []
    for fu in rows:
        delta = (
            now - fu.scheduled_date.replace(tzinfo=UTC)
            if fu.scheduled_date.tzinfo is None
            else now - fu.scheduled_date
        )
        days_overdue = max(0, delta.days)
        pending.append(
            PendingSurvey(
                follow_up_id=fu.id,
                adoption_request_id=fu.adoption_request_id,
                scheduled_date=fu.scheduled_date,
                day_offset=fu.day_offset,
                days_overdue=days_overdue,
            )
        )
    return pending


async def get_survey_stats(db: AsyncSession) -> SurveyStats:
    """Return aggregate survey dispatch and satisfaction statistics."""
    from sqlalchemy import func  # local import avoids polluting module namespace

    count_result = await db.execute(
        select(
            func.count(FollowUp.id).label("total"),
            func.count(FollowUp.survey_sent_at).label("sent"),
            func.count(FollowUp.survey_completed_at).label("completed"),
        )
    )
    row = count_result.one()
    total_scheduled = int(row.total)
    total_sent = int(row.sent)
    total_completed = int(row.completed)

    # Average scores — only from completed surveys
    avg_result = await db.execute(
        select(
            func.sum(FollowUp.welfare_score).label("welfare_sum"),
            func.sum(FollowUp.satisfaction_score).label("satisfaction_sum"),
            func.count(FollowUp.welfare_score).label("welfare_count"),
            func.count(FollowUp.satisfaction_score).label("satisfaction_count"),
        ).where(FollowUp.survey_completed_at.is_not(None))
    )
    avg_row = avg_result.one()
    avg_welfare = _safe_avg(float(avg_row.welfare_sum or 0), int(avg_row.welfare_count or 0))
    avg_satisfaction = _safe_avg(
        float(avg_row.satisfaction_sum or 0), int(avg_row.satisfaction_count or 0)
    )

    return SurveyStats(
        total_scheduled=total_scheduled,
        total_sent=total_sent,
        total_completed=total_completed,
        send_rate_pct=_safe_pct(total_sent, total_scheduled),
        completion_rate_pct=_safe_pct(total_completed, total_sent),
        avg_welfare_score=avg_welfare,
        avg_satisfaction_score=avg_satisfaction,
    )


async def mark_surveys_sent(
    db: AsyncSession,
    follow_up_ids: list[UUID],
) -> MarkSentResult:
    """Bulk mark follow-ups as having their survey sent.

    Sets survey_sent_at to now() and status to 'sent' for rows that:
    - match the provided IDs
    - have not already had their survey sent (survey_sent_at IS NULL)

    Returns counts of newly marked vs already-sent rows.
    """
    if not follow_up_ids:
        return MarkSentResult(marked_count=0, already_sent_count=0)

    now = datetime.now(UTC)

    # Count how many already have survey_sent_at set
    already_result = await db.execute(
        select(FollowUp).where(
            FollowUp.id.in_(follow_up_ids),
            FollowUp.survey_sent_at.is_not(None),
        )
    )
    already_sent_count = len(already_result.scalars().all())

    # Count rows that will be updated (those not yet sent)
    to_update_result = await db.execute(
        select(FollowUp).where(
            FollowUp.id.in_(follow_up_ids),
            FollowUp.survey_sent_at.is_(None),
        )
    )
    to_update_ids = [fu.id for fu in to_update_result.scalars()]
    marked_count = len(to_update_ids)

    if marked_count > 0:
        await db.execute(
            update(FollowUp)
            .where(FollowUp.id.in_(to_update_ids))
            .values(
                survey_sent_at=now,
                status=FollowUpStatus.SENT.value,
                updated_at=now,
            )
        )

    await db.flush()
    return MarkSentResult(marked_count=marked_count, already_sent_count=already_sent_count)


async def get_survey_results(
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0,
    min_score: int | None = None,
) -> list[SurveyResult]:
    """List completed survey responses, ordered newest first.

    Optionally filter to responses where welfare_score < min_score
    (useful for surfacing low-welfare cases needing follow-up).
    """
    query = (
        select(FollowUp)
        .where(FollowUp.survey_completed_at.is_not(None))
        .order_by(FollowUp.survey_completed_at.desc())
    )
    if min_score is not None:
        query = query.where(FollowUp.welfare_score < min_score)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)

    return [
        SurveyResult(
            follow_up_id=fu.id,
            adoption_request_id=fu.adoption_request_id,
            day_offset=fu.day_offset,
            welfare_score=fu.welfare_score,  # type: ignore[arg-type] — filtered by is_not(None)
            satisfaction_score=fu.satisfaction_score,  # type: ignore[arg-type]
            survey_completed_at=fu.survey_completed_at,  # type: ignore[arg-type]
            comments=fu.comments,
            issues_noted=fu.issues_noted,
        )
        for fu in result.scalars()
    ]
