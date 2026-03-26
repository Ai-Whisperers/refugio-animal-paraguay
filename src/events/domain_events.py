"""Concrete domain event classes for Refugio Animal Paraguay.

Each event class represents a meaningful domain occurrence. Events carry
all context needed for handlers to process them without querying the database.

Naming convention: PascalCase noun phrases describing what happened.
Event type convention: dot-notation domain.action (e.g., "adoption.status_changed").
"""

from dataclasses import dataclass, field

from .base import DomainEvent


@dataclass(frozen=True)
class AdoptionStatusChanged(DomainEvent):
    """Fired when an adoption request changes status.

    Payload keys:
        adoption_request_id: UUID of the adoption request
        animal_id: UUID of the animal
        adopter_id: UUID of the adopter
        old_status: Previous status string
        new_status: New status string
    """

    event_type: str = field(default="adoption.status_changed", init=False)


@dataclass(frozen=True)
class DonationReceived(DomainEvent):
    """Fired when a donation is successfully processed.

    Payload keys:
        donation_id: UUID of the donation
        donor_id: UUID of the donor
        amount_cents: Integer amount in smallest currency unit
        currency: ISO currency code (EUR, PYG, USD)
        payment_method: Payment method used
    """

    event_type: str = field(default="donation.received", init=False)


@dataclass(frozen=True)
class MedicalAlert(DomainEvent):
    """Fired when a medical condition requires attention.

    Payload keys:
        animal_id: UUID of the animal
        alert_type: Type of alert (vaccination_overdue, condition_critical, etc.)
        description: Human-readable alert description
        priority: Alert priority (low, medium, high, critical)
    """

    event_type: str = field(default="medical.alert", init=False)


@dataclass(frozen=True)
class VolunteerShiftCreated(DomainEvent):
    """Fired when a new volunteer shift is scheduled.

    Payload keys:
        shift_id: UUID of the shift
        volunteer_id: UUID of the volunteer
        start_time: ISO datetime of shift start
        end_time: ISO datetime of shift end
        task_type: Type of volunteer task
    """

    event_type: str = field(default="volunteer.shift_created", init=False)


@dataclass(frozen=True)
class AnimalIntake(DomainEvent):
    """Fired when a new animal is registered in the shelter.

    Payload keys:
        animal_id: UUID of the animal
        species: Animal species
        name: Animal name
        intake_reason: Reason for intake (stray, surrender, transfer, etc.)
    """

    event_type: str = field(default="animal.intake", init=False)
