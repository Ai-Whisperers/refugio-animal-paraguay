"""Pydantic schemas for post-adoption follow-up endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.db.models.follow_up import ReturnReasonCode

# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class FollowUpResponse(BaseModel):
    """Full follow-up record returned from list/detail endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    adoption_request_id: UUID
    scheduled_date: datetime
    day_offset: int
    status: str
    survey_sent_at: datetime | None = None
    survey_completed_at: datetime | None = None
    welfare_score: int | None = None
    satisfaction_score: int | None = None
    comments: str | None = None
    photo_url: str | None = None
    issues_noted: str | None = None
    return_date: datetime | None = None
    return_reason_code: str | None = None
    return_notes: str | None = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class SurveySubmission(BaseModel):
    """Adopter-submitted welfare survey."""

    welfare_score: int = Field(..., ge=1, le=5, description="Welfare assessment 1-5")
    satisfaction_score: int = Field(..., ge=1, le=5, description="Adopter satisfaction 1-5")
    comments: str | None = None
    photo_url: str | None = None
    issues_noted: str | None = None


class ReturnRecord(BaseModel):
    """Staff-recorded return/rehome event."""

    return_reason_code: ReturnReasonCode
    return_notes: str | None = None


# ---------------------------------------------------------------------------
# Analytics schemas
# ---------------------------------------------------------------------------


class AdoptionOutcomeStats(BaseModel):
    """Aggregated adoption outcome statistics."""

    total_completed_adoptions: int
    total_returned: int
    success_rate_pct: float
    return_rate_by_species: dict[str, float]
    average_welfare_score: float | None = None
    average_satisfaction_score: float | None = None
