"""Pydantic schemas for GDPR consent management."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.db.models.user_consent import ConsentMethod, ConsentStatus, ConsentType


class ConsentUpdate(BaseModel):
    """Request body for granting or revoking a single consent type."""

    consent_type: ConsentType
    granted: bool = Field(
        ...,
        description="True to grant consent, False to revoke.",
    )
    method: ConsentMethod = ConsentMethod.USER_SELF_SERVICE
    notes: str | None = None


class ConsentBulkUpdate(BaseModel):
    """Request body for updating multiple consent preferences at once."""

    consents: list[ConsentUpdate] = Field(
        ...,
        min_length=1,
        description="List of consent updates to apply.",
    )


class ConsentResponse(BaseModel):
    """Current state of a single consent type for a user."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    consent_type: ConsentType
    status: ConsentStatus
    opt_in_date: datetime
    opt_out_date: datetime | None
    method: ConsentMethod
    granted_by_staff_id: UUID | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class ConsentSummary(BaseModel):
    """Summary of all consent types for a user with their current status."""

    user_id: UUID
    consents: dict[ConsentType, bool] = Field(
        description="Map of consent type to active status (True = active, False = revoked/not set)."
    )


class ConsentHistoryEntry(BaseModel):
    """A single entry in the consent change history."""

    consent_type: ConsentType
    action: str = Field(description="'granted' or 'revoked'")
    method: ConsentMethod
    timestamp: datetime
    ip_address: str | None
    user_agent: str | None
    notes: str | None
