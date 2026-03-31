"""Trial period management endpoints.

Admin endpoints:
  POST  /api/admin/adoptions/{id}/trial-period  -- create trial
  GET   /api/admin/adoptions/{id}/trial          -- get trial with check-ins
  PATCH /api/admin/adoptions/{id}/trial          -- mark passed/failed/extend

Adopter endpoints:
  GET   /api/adoptions/{id}/trial-period         -- get trial info
  POST  /api/adoptions/{id}/trial-checkin        -- submit check-in
"""

import logging
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.adoption_request import AdoptionRequest
from src.db.models.trial_period import (
    DEFAULT_CHECK_IN_DAYS,
    DEFAULT_TRIAL_DAYS,
    TrialCheckIn,
    TrialPeriod,
)
from src.db.session import get_async_session

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class TrialPeriodCreateRequest(BaseModel):
    """Payload for creating a trial period."""

    duration_days: int = Field(default=DEFAULT_TRIAL_DAYS, ge=7, le=60)
    check_in_days: list[int] = Field(default_factory=lambda: list(DEFAULT_CHECK_IN_DAYS))
    notes: str | None = None


class CheckInRequest(BaseModel):
    """Payload for adopter check-in."""

    how_is_animal: str = Field(..., min_length=5, max_length=2000)
    photos: list[str] = Field(default_factory=list, max_length=3)
    issues: str | None = Field(default=None, max_length=2000)
    happiness_rating: int = Field(..., ge=1, le=5)


class TrialStatusUpdateRequest(BaseModel):
    """Payload for updating trial status."""

    status: str = Field(..., pattern="^(passed|failed|extended)$")
    extend_days: int | None = Field(default=None, ge=1, le=30)
    notes: str | None = None


class CheckInResponse(BaseModel):
    """Check-in response."""

    id: UUID
    day_number: int
    how_is_animal: str
    photos: list[str]
    issues: str | None
    happiness_rating: int
    has_issues: bool
    created_at: str

    model_config = {"from_attributes": True}


class TrialPeriodResponse(BaseModel):
    """Trial period response."""

    id: UUID
    adoption_request_id: UUID
    start_date: str
    end_date: str
    check_in_schedule: list
    status: str
    notes: str | None
    check_ins: list[CheckInResponse] = Field(default_factory=list)
    created_at: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _serialise_checkin(c: TrialCheckIn) -> dict:
    """Convert check-in to response dict."""
    return {
        "id": c.id,
        "day_number": c.day_number,
        "how_is_animal": c.how_is_animal,
        "photos": c.photos or [],
        "issues": c.issues,
        "happiness_rating": c.happiness_rating,
        "has_issues": c.has_issues,
        "created_at": c.created_at.isoformat(),
    }


def _serialise_trial(t: TrialPeriod, check_ins: list | None = None) -> dict:
    """Convert trial period to response dict."""
    return {
        "id": t.id,
        "adoption_request_id": t.adoption_request_id,
        "start_date": t.start_date.isoformat(),
        "end_date": t.end_date.isoformat(),
        "check_in_schedule": t.check_in_schedule or [],
        "status": t.status,
        "notes": t.notes,
        "check_ins": [_serialise_checkin(c) for c in (check_ins or [])],
        "created_at": t.created_at.isoformat(),
    }


async def _get_trial_for_adoption(db: AsyncSession, adoption_id: UUID) -> TrialPeriod | None:
    """Find the active/latest trial for an adoption."""
    stmt = (
        select(TrialPeriod)
        .where(
            TrialPeriod.adoption_request_id == adoption_id,
            TrialPeriod.is_deleted.is_(False),
        )
        .order_by(TrialPeriod.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _get_check_ins(db: AsyncSession, trial_id: UUID) -> list[TrialCheckIn]:
    """Get all check-ins for a trial, ordered by day."""
    stmt = (
        select(TrialCheckIn)
        .where(TrialCheckIn.trial_period_id == trial_id)
        .order_by(TrialCheckIn.day_number)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Admin Router
# ---------------------------------------------------------------------------

admin_router = APIRouter(
    prefix="/api/admin/adoptions",
    tags=["admin-trial-periods"],
    dependencies=[Depends(require_staff)],
)


@admin_router.post(
    "/{adoption_id}/trial-period",
    response_model=TrialPeriodResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a trial period for an adoption",
)
async def create_trial_period(
    adoption_id: UUID,
    payload: TrialPeriodCreateRequest,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Create a new trial period with check-in schedule."""
    # Verify adoption exists
    adoption = await db.get(AdoptionRequest, adoption_id)
    if adoption is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Adoption request not found"},
        )

    # Check no active trial exists
    existing = await _get_trial_for_adoption(db, adoption_id)
    if existing and existing.status in ("active", "extended"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "Active trial already exists for this adoption"},
        )

    today = date.today()
    schedule = [{"day": d, "status": "pending"} for d in payload.check_in_days]

    trial = TrialPeriod(
        adoption_request_id=adoption_id,
        start_date=today,
        end_date=today + timedelta(days=payload.duration_days),
        check_in_schedule=schedule,
        status="active",
        notes=payload.notes,
    )
    db.add(trial)
    await db.flush()
    await db.refresh(trial)
    return _serialise_trial(trial)


@admin_router.get(
    "/{adoption_id}/trial",
    response_model=TrialPeriodResponse,
    summary="Get trial period with check-ins (admin)",
)
async def get_trial_admin(
    adoption_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Return trial period with all check-in responses."""
    trial = await _get_trial_for_adoption(db, adoption_id)
    if trial is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "No trial period found for this adoption"},
        )
    check_ins = await _get_check_ins(db, trial.id)
    return _serialise_trial(trial, check_ins)


@admin_router.patch(
    "/{adoption_id}/trial",
    response_model=TrialPeriodResponse,
    summary="Update trial status (pass/fail/extend)",
)
async def update_trial_status(
    adoption_id: UUID,
    payload: TrialStatusUpdateRequest,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Mark trial as passed, failed, or extended."""
    trial = await _get_trial_for_adoption(db, adoption_id)
    if trial is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "No trial period found"},
        )

    if trial.status not in ("active", "extended"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": f"Cannot update trial with status '{trial.status}'"},
        )

    trial.status = payload.status

    if payload.status == "extended" and payload.extend_days:
        trial.end_date = trial.end_date + timedelta(days=payload.extend_days)
        # Add new check-in at midpoint of extension
        mid_day = (trial.end_date - trial.start_date).days
        schedule = trial.check_in_schedule or []
        schedule.append({"day": mid_day, "status": "pending"})
        trial.check_in_schedule = schedule

    if payload.notes:
        existing_notes = trial.notes or ""
        trial.notes = f"{existing_notes}\n[{datetime.now(UTC).isoformat()}] {payload.notes}".strip()

    await db.flush()
    await db.refresh(trial)

    check_ins = await _get_check_ins(db, trial.id)
    return _serialise_trial(trial, check_ins)


# ---------------------------------------------------------------------------
# Adopter Router
# ---------------------------------------------------------------------------

public_router = APIRouter(
    prefix="/api/adoptions",
    tags=["trial-periods"],
)


@public_router.get(
    "/{adoption_id}/trial-period",
    response_model=TrialPeriodResponse,
    summary="Get trial period info (adopter)",
)
async def get_trial_public(
    adoption_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Return trial period details for the adopter."""
    trial = await _get_trial_for_adoption(db, adoption_id)
    if trial is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "No trial period found"},
        )
    check_ins = await _get_check_ins(db, trial.id)
    return _serialise_trial(trial, check_ins)


@public_router.post(
    "/{adoption_id}/trial-checkin",
    response_model=CheckInResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a trial check-in",
)
async def submit_check_in(
    adoption_id: UUID,
    payload: CheckInRequest,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Submit a check-in response during the trial period."""
    trial = await _get_trial_for_adoption(db, adoption_id)
    if trial is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "No trial period found"},
        )

    if trial.status not in ("active", "extended"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "Trial is not active"},
        )

    # Calculate which day of the trial we're on
    today = date.today()
    day_number = (today - trial.start_date).days

    has_issues = bool(payload.issues and payload.issues.strip())

    check_in = TrialCheckIn(
        trial_period_id=trial.id,
        day_number=day_number,
        how_is_animal=payload.how_is_animal,
        photos=payload.photos,
        issues=payload.issues,
        happiness_rating=payload.happiness_rating,
        has_issues=has_issues,
    )
    db.add(check_in)
    await db.flush()
    await db.refresh(check_in)

    # Update schedule status
    schedule = trial.check_in_schedule or []
    for entry in schedule:
        if entry.get("day") == day_number or (
            entry.get("status") == "pending" and abs(entry.get("day", 0) - day_number) <= 1
        ):
            entry["status"] = "completed"
            break
    trial.check_in_schedule = schedule
    await db.flush()

    if has_issues:
        logger.warning(
            "Trial check-in reported issues for adoption %s (trial %s, day %d)",
            adoption_id,
            trial.id,
            day_number,
        )

    return _serialise_checkin(check_in)
