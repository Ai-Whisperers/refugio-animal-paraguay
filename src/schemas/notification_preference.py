"""Pydantic schemas for notification preferences API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PreferenceItem(BaseModel):
    """Single notification preference entry."""

    notification_type: str = Field(
        ...,
        pattern="^(adoption_request_created|adoption_status_changed|"
        "donation_received|donation_refunded|"
        "animal_intake_completed|animal_status_changed|"
        "system_alert|gdpr_request)$",
    )
    channel: str = Field(
        ...,
        pattern="^(in_app|email)$",
    )
    enabled: bool


class PreferenceResponse(BaseModel):
    """Single preference in API responses."""

    notification_type: str
    channel: str
    enabled: bool

    model_config = ConfigDict(from_attributes=True)


class PreferenceListResponse(BaseModel):
    """Full preference matrix response."""

    preferences: list[PreferenceResponse]


class PreferenceBulkUpdate(BaseModel):
    """Request to update multiple preferences at once."""

    preferences: list[PreferenceItem] = Field(
        ...,
        min_length=1,
        max_length=50,
    )
