"""Concrete domain event classes.

Each class sets a default event_type and aggregate_type, so callers only need
to provide the event-specific payload and aggregate_id.

Usage:
    event = AdoptionStatusChanged(
        payload={"old_status": "pending", "new_status": "approved"},
        aggregate_id=adoption_request_id,
        actor_id=staff_user_id,
    )
    await event_bus.publish(event)
"""

from uuid import UUID

from src.events.types import DomainEvent, EventType


class AdoptionRequestCreated(DomainEvent):
    """Published when a new adoption request is submitted."""

    event_type: EventType = EventType.ADOPTION_REQUEST_CREATED
    aggregate_type: str = "adoption_request"


class AdoptionStatusChanged(DomainEvent):
    """Published when an adoption request transitions to a new status."""

    event_type: EventType = EventType.ADOPTION_STATUS_CHANGED
    aggregate_type: str = "adoption_request"


class DonationReceived(DomainEvent):
    """Published when a donation payment is confirmed."""

    event_type: EventType = EventType.DONATION_RECEIVED
    aggregate_type: str = "donation"


class MedicalAlertCreated(DomainEvent):
    """Published when a medical alert is created for an animal."""

    event_type: EventType = EventType.MEDICAL_ALERT_CREATED
    aggregate_type: str = "medical_record"


class VolunteerShiftCreated(DomainEvent):
    """Published when a new volunteer shift is scheduled."""

    event_type: EventType = EventType.VOLUNTEER_SHIFT_CREATED
    aggregate_type: str = "volunteer_shift"


class VolunteerShiftCompleted(DomainEvent):
    """Published when a volunteer completes their shift."""

    event_type: EventType = EventType.VOLUNTEER_SHIFT_COMPLETED
    aggregate_type: str = "volunteer_shift"


class AnimalIntakeCompleted(DomainEvent):
    """Published when an animal intake process is completed."""

    event_type: EventType = EventType.ANIMAL_INTAKE_COMPLETED
    aggregate_type: str = "animal"


def create_adoption_request_created(
    aggregate_id: UUID,
    adopter_name: str,
    animal_name: str,
    adopter_email: str | None = None,
    actor_id: UUID | None = None,
) -> AdoptionRequestCreated:
    """Factory for AdoptionRequestCreated events with typed payload."""
    return AdoptionRequestCreated(
        payload={
            "adopter_name": adopter_name,
            "animal_name": animal_name,
            "adopter_email": adopter_email,
        },
        aggregate_id=aggregate_id,
        actor_id=actor_id,
    )


def create_adoption_status_changed(
    aggregate_id: UUID,
    old_status: str,
    new_status: str,
    actor_id: UUID | None = None,
    notes: str | None = None,
) -> AdoptionStatusChanged:
    """Factory for AdoptionStatusChanged events with typed payload."""
    payload: dict[str, str | None] = {
        "old_status": old_status,
        "new_status": new_status,
    }
    if notes:
        payload["notes"] = notes
    return AdoptionStatusChanged(
        payload=payload,
        aggregate_id=aggregate_id,
        actor_id=actor_id,
    )


class DonationAllocated(DomainEvent):
    """Published when a donation is allocated to an expense."""

    event_type: EventType = EventType.DONATION_ALLOCATED
    aggregate_type: str = "donation"


def create_donation_allocated(
    aggregate_id: UUID,
    donation_id: UUID,
    expense_id: UUID,
    amount_cents: int,
    currency: str,
    expense_description: str,
    donor_id: UUID | None = None,
    donor_email: str | None = None,
    actor_id: UUID | None = None,
) -> DonationAllocated:
    """Factory for DonationAllocated events with typed payload."""
    return DonationAllocated(
        payload={
            "donation_id": str(donation_id),
            "expense_id": str(expense_id),
            "amount_cents": amount_cents,
            "currency": currency,
            "expense_description": expense_description,
            "donor_id": str(donor_id) if donor_id else None,
            "donor_email": donor_email,
        },
        aggregate_id=aggregate_id,
        actor_id=actor_id,
    )


def create_donation_received(
    aggregate_id: UUID,
    amount: str,
    currency: str,
    donor_id: UUID | None = None,
    actor_id: UUID | None = None,
) -> DonationReceived:
    """Factory for DonationReceived events with typed payload."""
    return DonationReceived(
        payload={
            "amount": amount,
            "currency": currency,
            "donor_id": str(donor_id) if donor_id else None,
        },
        aggregate_id=aggregate_id,
        actor_id=actor_id,
    )
