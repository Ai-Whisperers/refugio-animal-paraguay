"""Domain event schema and event type enumeration.

DomainEvent is the base class for all domain events. Every event carries:
  - id: unique event identifier (UUID4)
  - event_type: machine-readable type from EventType enum
  - payload: event-specific data
  - timestamp: ISO 8601 creation time
  - actor_id: who/what triggered the event
  - idempotency_key: prevents duplicate processing on retries
  - aggregate_id: ID of the domain object this event relates to
  - aggregate_type: type name of the aggregate (e.g., "adoption_request")
"""

import enum
from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EventType(enum.StrEnum):
    """All domain event types. Dot-separated namespace convention."""

    # Adoption domain
    ADOPTION_STATUS_CHANGED = "adoption.status_changed"
    ADOPTION_REQUEST_CREATED = "adoption.request_created"

    # Donation domain
    DONATION_RECEIVED = "donation.received"
    DONATION_REFUNDED = "donation.refunded"

    # Medical domain
    MEDICAL_ALERT_CREATED = "medical.alert_created"
    MEDICAL_RECORD_ADDED = "medical.record_added"

    # Volunteer domain
    VOLUNTEER_SHIFT_CREATED = "volunteer.shift_created"
    VOLUNTEER_SHIFT_COMPLETED = "volunteer.shift_completed"

    # Subscription domain
    SUBSCRIPTION_PAYMENT_FAILED = "subscription.payment_failed"
    SUBSCRIPTION_CANCELLED_DUNNING = "subscription.cancelled_dunning"

    # Animal domain
    ANIMAL_INTAKE_COMPLETED = "animal.intake_completed"
    ANIMAL_STATUS_CHANGED = "animal.status_changed"


class DomainEvent(BaseModel):
    """Base schema for all domain events.

    Subclasses should set event_type as a class-level default and extend
    payload with event-specific fields.
    """

    id: UUID = Field(default_factory=uuid4, description="Unique event identifier")
    event_type: EventType = Field(..., description="Machine-readable event type")
    payload: dict = Field(default_factory=dict, description="Event-specific data")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the event occurred (UTC)",
    )
    actor_id: UUID | None = Field(
        default=None,
        description="User or system that triggered the event",
    )
    idempotency_key: UUID = Field(
        default_factory=uuid4,
        description="Prevents duplicate processing on retries",
    )
    aggregate_id: UUID | None = Field(
        default=None,
        description="ID of the domain object this event relates to",
    )
    aggregate_type: str | None = Field(
        default=None,
        description="Type name of the aggregate (e.g., 'adoption_request')",
    )

    model_config = {"frozen": True}
