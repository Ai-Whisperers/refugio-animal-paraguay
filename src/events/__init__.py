"""Domain event bus — publish/subscribe infrastructure for domain events.

Provides:
  - DomainEvent: Base event schema with metadata (id, type, payload, timestamp, etc.)
  - EventType: Enum of all domain event types
  - EventBus: In-process async event dispatcher
  - Concrete event classes: AdoptionStatusChanged, DonationReceived, etc.
"""

from src.events.bus import EventBus
from src.events.dependencies import get_event_bus
from src.events.domain_events import (
    AdoptionStatusChanged,
    AnimalIntakeCompleted,
    DonationReceived,
    MedicalAlertCreated,
    VolunteerShiftCompleted,
    VolunteerShiftCreated,
)
from src.events.types import DomainEvent, EventType

__all__ = [
    "AdoptionStatusChanged",
    "AnimalIntakeCompleted",
    "DomainEvent",
    "DonationReceived",
    "EventBus",
    "EventType",
    "MedicalAlertCreated",
    "VolunteerShiftCompleted",
    "VolunteerShiftCreated",
    "get_event_bus",
]
