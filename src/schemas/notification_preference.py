"""Pydantic schemas for notification preferences API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

FREQUENCY_PATTERN = "^(immediate|daily_digest|weekly)$"
CHANNEL_PATTERN = "^(in_app|email)$"


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


class UnsubscribeLinkResponse(BaseModel):
    """Response containing a signed one-click unsubscribe URL."""

    unsubscribe_url: str = Field(
        ...,
        description="Signed URL to disable all email notifications. Valid for 30 days.",
    )
    expires_in_days: int = Field(
        default=30,
        description="Number of days until the unsubscribe link expires.",
    )


class UnsubscribeResult(BaseModel):
    """Response after successfully processing an unsubscribe request."""

    message: str = Field(
        default="Successfully unsubscribed from all email notifications.",
        description="Human-readable confirmation message.",
    )
    preferences_updated: int = Field(
        ...,
        description="Number of email notification preferences set to disabled.",
    )


class FrequencyItem(BaseModel):
    """Frequency setting for one channel."""

    channel: str = Field(..., pattern=CHANNEL_PATTERN)
    frequency: str = Field(..., pattern=FREQUENCY_PATTERN)


class FrequencyResponse(BaseModel):
    """Single channel frequency in API responses."""

    channel: str
    frequency: str

    model_config = ConfigDict(from_attributes=True)


class FrequencyListResponse(BaseModel):
    """All channel frequency settings response."""

    frequencies: list[FrequencyResponse]


class FrequencyBulkUpdate(BaseModel):
    """Request to update frequency settings for one or more channels."""

    frequencies: list[FrequencyItem] = Field(
        ...,
        min_length=1,
        max_length=10,
    )
