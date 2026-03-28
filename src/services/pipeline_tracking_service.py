"""Service layer for adoption pipeline status tracking.

Handles advancing adoption requests through pipeline stages,
recording transition history, detecting timeouts, and
providing stage history for audit trails.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Valid transition actions
ACTION_ADVANCE = "advance"
ACTION_REJECT = "reject"
ACTION_RESET = "reset"
VALID_ACTIONS = {ACTION_ADVANCE, ACTION_REJECT, ACTION_RESET}

# Rejection pseudo-status used when an application is rejected at any stage
REJECTION_STATUS = "rejected"


class PipelineTrackingError(Exception):
    """Base error for pipeline tracking operations."""


class AdoptionNotFoundError(PipelineTrackingError):
    """Raised when the adoption request does not exist."""


class StageNotFoundError(PipelineTrackingError):
    """Raised when a pipeline stage does not exist or is inactive."""


class InvalidTransitionError(PipelineTrackingError):
    """Raised when a stage transition is not valid."""


class AlreadyCompletedError(PipelineTrackingError):
    """Raised when trying to advance a completed or rejected adoption."""


async def get_adoption_with_stage(
    db: AsyncSession,
    adoption_request_id: UUID,
) -> dict:
    """Fetch adoption request with its current stage info.

    Returns a dict with adoption fields and current_stage details.
    Raises AdoptionNotFoundError if not found.
    """
    from src.db.models.adoption_request import AdoptionRequest

    result = await db.execute(
        select(AdoptionRequest).where(AdoptionRequest.id == adoption_request_id)
    )
    adoption = result.scalar_one_or_none()
    if adoption is None:
        raise AdoptionNotFoundError(f"Adoption request {adoption_request_id} not found")

    current_stage = None
    days_in_stage = None
    if hasattr(adoption, "current_stage_id") and adoption.current_stage_id:
        from src.db.models.adoption_pipeline import AdoptionPipelineStage

        stage_result = await db.execute(
            select(AdoptionPipelineStage).where(
                AdoptionPipelineStage.id == adoption.current_stage_id
            )
        )
        stage = stage_result.scalar_one_or_none()
        if stage:
            current_stage = {
                "id": stage.id,
                "name": stage.name,
                "position": stage.position,
                "color": stage.color,
                "requires_approval": stage.requires_approval,
                "max_days": stage.max_days,
            }
        if hasattr(adoption, "current_stage_started_at") and adoption.current_stage_started_at:
            delta = datetime.now(UTC) - adoption.current_stage_started_at
            days_in_stage = delta.days

    return {
        "id": adoption.id,
        "animal_id": adoption.animal_id,
        "adopter_id": adoption.adopter_id,
        "status": adoption.status,
        "current_stage_id": getattr(adoption, "current_stage_id", None),
        "current_stage_started_at": getattr(adoption, "current_stage_started_at", None),
        "current_stage": current_stage,
        "days_in_current_stage": days_in_stage,
    }


async def get_next_stage(
    db: AsyncSession,
    current_stage_id: UUID | None,
) -> dict | None:
    """Find the next active stage after the current one.

    If current_stage_id is None, returns the first active stage.
    Returns None if there is no next stage (adoption is at the last stage).
    """
    from src.db.models.adoption_pipeline import AdoptionPipelineStage

    if current_stage_id is None:
        # First stage
        result = await db.execute(
            select(AdoptionPipelineStage)
            .where(AdoptionPipelineStage.is_active.is_(True))
            .order_by(AdoptionPipelineStage.position.asc())
            .limit(1)
        )
        stage = result.scalar_one_or_none()
    else:
        # Get current position
        current = await db.execute(
            select(AdoptionPipelineStage).where(AdoptionPipelineStage.id == current_stage_id)
        )
        current_stage = current.scalar_one_or_none()
        if current_stage is None:
            return None

        result = await db.execute(
            select(AdoptionPipelineStage)
            .where(
                AdoptionPipelineStage.is_active.is_(True),
                AdoptionPipelineStage.position > current_stage.position,
            )
            .order_by(AdoptionPipelineStage.position.asc())
            .limit(1)
        )
        stage = result.scalar_one_or_none()

    if stage is None:
        return None

    return {
        "id": stage.id,
        "name": stage.name,
        "position": stage.position,
        "color": stage.color,
        "requires_approval": stage.requires_approval,
        "max_days": stage.max_days,
    }


async def advance_adoption(
    db: AsyncSession,
    adoption_request_id: UUID,
    user_id: UUID | None = None,
    notes: str | None = None,
) -> dict:
    """Advance an adoption request to the next pipeline stage.

    Creates a stage log entry, updates the adoption request's current
    stage, and returns the transition details.

    Raises AlreadyCompletedError if adoption is rejected/cancelled.
    Raises InvalidTransitionError if there is no next stage.
    """
    from src.db.models.adoption_request import AdoptionRequest
    from src.db.models.adoption_stage_log import AdoptionStageLog

    result = await db.execute(
        select(AdoptionRequest).where(AdoptionRequest.id == adoption_request_id)
    )
    adoption = result.scalar_one_or_none()
    if adoption is None:
        raise AdoptionNotFoundError(f"Adoption request {adoption_request_id} not found")

    if adoption.status in ("rejected", "cancelled"):
        raise AlreadyCompletedError(f"Cannot advance adoption with status '{adoption.status}'")

    current_stage_id = getattr(adoption, "current_stage_id", None)
    next_stage = await get_next_stage(db, current_stage_id)

    if next_stage is None:
        raise InvalidTransitionError("No next stage available — adoption is at the final stage")

    now = datetime.now(UTC)

    # Create transition log
    log_entry = AdoptionStageLog(
        adoption_request_id=adoption_request_id,
        from_stage_id=current_stage_id,
        to_stage_id=next_stage["id"],
        action=ACTION_ADVANCE,
        notes=notes,
        transitioned_by=user_id,
        transitioned_at=now,
    )
    db.add(log_entry)

    # Update adoption request
    adoption.current_stage_id = next_stage["id"]
    adoption.current_stage_started_at = now

    # If this is the first stage, set status to approved (in pipeline)
    if adoption.status == "pending":
        adoption.status = "approved"

    await db.flush()

    logger.info(
        "Adoption %s advanced to stage '%s'",
        adoption_request_id,
        next_stage["name"],
    )

    return {
        "adoption_request_id": adoption_request_id,
        "from_stage_id": current_stage_id,
        "to_stage_id": next_stage["id"],
        "to_stage_name": next_stage["name"],
        "action": ACTION_ADVANCE,
        "notes": notes,
        "transitioned_at": now,
    }


async def reject_adoption(
    db: AsyncSession,
    adoption_request_id: UUID,
    reason: str,
    user_id: UUID | None = None,
) -> dict:
    """Reject an adoption request at any stage.

    Creates a rejection log entry and sets adoption status to rejected.

    Raises AdoptionNotFoundError if not found.
    Raises AlreadyCompletedError if already rejected/cancelled.
    """
    from src.db.models.adoption_request import AdoptionRequest
    from src.db.models.adoption_stage_log import AdoptionStageLog

    result = await db.execute(
        select(AdoptionRequest).where(AdoptionRequest.id == adoption_request_id)
    )
    adoption = result.scalar_one_or_none()
    if adoption is None:
        raise AdoptionNotFoundError(f"Adoption request {adoption_request_id} not found")

    if adoption.status in ("rejected", "cancelled"):
        raise AlreadyCompletedError(f"Adoption already has status '{adoption.status}'")

    now = datetime.now(UTC)
    current_stage_id = getattr(adoption, "current_stage_id", None)

    # Create rejection log
    log_entry = AdoptionStageLog(
        adoption_request_id=adoption_request_id,
        from_stage_id=current_stage_id,
        to_stage_id=None,
        action=ACTION_REJECT,
        notes=reason,
        transitioned_by=user_id,
        transitioned_at=now,
    )
    db.add(log_entry)

    # Update adoption status
    adoption.status = REJECTION_STATUS
    adoption.decided_at = now

    await db.flush()

    logger.info(
        "Adoption %s rejected at stage %s",
        adoption_request_id,
        current_stage_id,
    )

    return {
        "adoption_request_id": adoption_request_id,
        "from_stage_id": current_stage_id,
        "action": ACTION_REJECT,
        "reason": reason,
        "transitioned_at": now,
    }


async def get_stage_history(
    db: AsyncSession,
    adoption_request_id: UUID,
) -> list[dict]:
    """Return all stage transitions for an adoption request, ordered by time.

    Raises AdoptionNotFoundError if the adoption request does not exist.
    """
    from src.db.models.adoption_request import AdoptionRequest
    from src.db.models.adoption_stage_log import AdoptionStageLog

    # Verify adoption exists
    exists_result = await db.execute(
        select(AdoptionRequest.id).where(AdoptionRequest.id == adoption_request_id)
    )
    if exists_result.scalar_one_or_none() is None:
        raise AdoptionNotFoundError(f"Adoption request {adoption_request_id} not found")

    result = await db.execute(
        select(AdoptionStageLog)
        .where(AdoptionStageLog.adoption_request_id == adoption_request_id)
        .order_by(AdoptionStageLog.transitioned_at.asc())
    )
    logs = result.scalars().all()

    return [
        {
            "id": log.id,
            "adoption_request_id": log.adoption_request_id,
            "from_stage_id": log.from_stage_id,
            "to_stage_id": log.to_stage_id,
            "action": log.action,
            "notes": log.notes,
            "transitioned_by": log.transitioned_by,
            "transitioned_at": log.transitioned_at,
        }
        for log in logs
    ]


async def get_timed_out_adoptions(
    db: AsyncSession,
) -> list[dict]:
    """Find adoption requests that have exceeded their stage's max_days.

    Returns adoptions where current_stage.max_days is set and
    the adoption has been in that stage for longer than allowed.
    """
    from src.db.models.adoption_pipeline import AdoptionPipelineStage
    from src.db.models.adoption_request import AdoptionRequest

    # Build a query joining adoption_requests with their current stage
    now = datetime.now(UTC)

    query = (
        select(
            AdoptionRequest.id,
            AdoptionRequest.animal_id,
            AdoptionRequest.adopter_id,
            AdoptionPipelineStage.id.label("stage_id"),
            AdoptionPipelineStage.name.label("stage_name"),
            AdoptionPipelineStage.max_days,
            AdoptionRequest.current_stage_started_at,
        )
        .join(
            AdoptionPipelineStage,
            AdoptionRequest.current_stage_id == AdoptionPipelineStage.id,
        )
        .where(
            AdoptionRequest.status.notin_(["rejected", "cancelled"]),
            AdoptionRequest.current_stage_id.isnot(None),
            AdoptionRequest.current_stage_started_at.isnot(None),
            AdoptionPipelineStage.max_days.isnot(None),
        )
    )

    result = await db.execute(query)
    rows = result.all()

    timed_out = []
    for row in rows:
        if row.current_stage_started_at is None or row.max_days is None:
            continue
        days_in_stage = (now - row.current_stage_started_at).days
        if days_in_stage > row.max_days:
            timed_out.append(
                {
                    "adoption_request_id": row.id,
                    "animal_id": row.animal_id,
                    "adopter_id": row.adopter_id,
                    "stage_id": row.stage_id,
                    "stage_name": row.stage_name,
                    "max_days": row.max_days,
                    "days_in_stage": days_in_stage,
                    "overdue_by": days_in_stage - row.max_days,
                }
            )

    return timed_out


async def get_pipeline_summary(
    db: AsyncSession,
) -> list[dict]:
    """Get a summary of adoption requests grouped by current pipeline stage.

    Returns count of adoptions in each stage, useful for dashboard views.
    """
    from src.db.models.adoption_pipeline import AdoptionPipelineStage
    from src.db.models.adoption_request import AdoptionRequest

    query = (
        select(
            AdoptionPipelineStage.id,
            AdoptionPipelineStage.name,
            AdoptionPipelineStage.position,
            AdoptionPipelineStage.color,
            func.count(AdoptionRequest.id).label("adoption_count"),
        )
        .outerjoin(
            AdoptionRequest,
            (AdoptionRequest.current_stage_id == AdoptionPipelineStage.id)
            & (AdoptionRequest.status.notin_(["rejected", "cancelled"])),
        )
        .where(AdoptionPipelineStage.is_active.is_(True))
        .group_by(
            AdoptionPipelineStage.id,
            AdoptionPipelineStage.name,
            AdoptionPipelineStage.position,
            AdoptionPipelineStage.color,
        )
        .order_by(AdoptionPipelineStage.position.asc())
    )

    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "stage_id": row.id,
            "stage_name": row.name,
            "position": row.position,
            "color": row.color,
            "adoption_count": row.adoption_count,
        }
        for row in rows
    ]
