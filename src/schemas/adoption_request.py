"""Pydantic schemas for the AdoptionRequest resource."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.db.models.adoption_request import AdoptionRequestStatus


class AdoptionRequestCreate(BaseModel):
    """Fields required when submitting a new adoption request."""

    animal_id: UUID
    adopter_id: UUID
    notes: str | None = None


class AdoptionRequestStatusUpdate(BaseModel):
    """Payload for the PATCH …/status endpoint — changes workflow state."""

    status: AdoptionRequestStatus


class AdoptionRequestResponse(BaseModel):
    """Shape returned by every AdoptionRequest endpoint."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    animal_id: UUID
    adopter_id: UUID
    status: AdoptionRequestStatus
    submitted_at: datetime
    decided_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
