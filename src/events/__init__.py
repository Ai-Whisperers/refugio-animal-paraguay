"""Domain event bus infrastructure for Refugio Animal Paraguay.

Provides an in-process async event dispatcher that decouples domain actions
from their side effects (notifications, audit logging, dashboard updates).

The bus is designed for upgrade to Redis pub/sub without handler changes.
"""

from .base import DomainEvent, EventBus, event_bus
from .domain_events import (
    AdoptionStatusChanged,
    AnimalIntake,
    DonationReceived,
    MedicalAlert,
    VolunteerShiftCreated,
)

__all__ = [
    "AdoptionStatusChanged",
    "AnimalIntake",
    "DomainEvent",
    "DonationReceived",
    "EventBus",
    "MedicalAlert",
    "VolunteerShiftCreated",
    "event_bus",
]
