"""Unit tests for concrete domain event classes and factory functions."""

from uuid import uuid4

from src.events.domain_events import (
    AdoptionStatusChanged,
    AnimalIntakeCompleted,
    DonationReceived,
    MedicalAlertCreated,
    VolunteerShiftCompleted,
    VolunteerShiftCreated,
    create_adoption_status_changed,
    create_donation_received,
)
from src.events.types import EventType


class TestConcreteEventClasses:
    """Each concrete event class sets correct defaults."""

    def test_adoption_status_changed_defaults(self) -> None:
        event = AdoptionStatusChanged(
            payload={"old_status": "pending", "new_status": "approved"},
            aggregate_id=uuid4(),
        )
        assert event.event_type == EventType.ADOPTION_STATUS_CHANGED
        assert event.aggregate_type == "adoption_request"

    def test_donation_received_defaults(self) -> None:
        event = DonationReceived(
            payload={"amount": "50.00", "currency": "EUR"},
            aggregate_id=uuid4(),
        )
        assert event.event_type == EventType.DONATION_RECEIVED
        assert event.aggregate_type == "donation"

    def test_medical_alert_created_defaults(self) -> None:
        event = MedicalAlertCreated(
            payload={"severity": "high"},
            aggregate_id=uuid4(),
        )
        assert event.event_type == EventType.MEDICAL_ALERT_CREATED
        assert event.aggregate_type == "medical_record"

    def test_volunteer_shift_created_defaults(self) -> None:
        event = VolunteerShiftCreated(
            payload={"date": "2026-04-01"},
            aggregate_id=uuid4(),
        )
        assert event.event_type == EventType.VOLUNTEER_SHIFT_CREATED
        assert event.aggregate_type == "volunteer_shift"

    def test_volunteer_shift_completed_defaults(self) -> None:
        event = VolunteerShiftCompleted(
            payload={"hours": 4},
            aggregate_id=uuid4(),
        )
        assert event.event_type == EventType.VOLUNTEER_SHIFT_COMPLETED
        assert event.aggregate_type == "volunteer_shift"

    def test_animal_intake_completed_defaults(self) -> None:
        event = AnimalIntakeCompleted(
            payload={"species": "dog"},
            aggregate_id=uuid4(),
        )
        assert event.event_type == EventType.ANIMAL_INTAKE_COMPLETED
        assert event.aggregate_type == "animal"


class TestFactoryFunctions:
    """Factory functions build events with typed payload fields."""

    def test_create_adoption_status_changed(self) -> None:
        aggregate_id = uuid4()
        actor_id = uuid4()
        event = create_adoption_status_changed(
            aggregate_id=aggregate_id,
            old_status="pending",
            new_status="approved",
            actor_id=actor_id,
        )
        assert isinstance(event, AdoptionStatusChanged)
        assert event.aggregate_id == aggregate_id
        assert event.actor_id == actor_id
        assert event.payload == {"old_status": "pending", "new_status": "approved"}

    def test_create_adoption_status_changed_without_actor(self) -> None:
        event = create_adoption_status_changed(
            aggregate_id=uuid4(),
            old_status="pending",
            new_status="rejected",
        )
        assert event.actor_id is None

    def test_create_donation_received(self) -> None:
        aggregate_id = uuid4()
        donor_id = uuid4()
        actor_id = uuid4()
        event = create_donation_received(
            aggregate_id=aggregate_id,
            amount="250.00",
            currency="EUR",
            donor_id=donor_id,
            actor_id=actor_id,
        )
        assert isinstance(event, DonationReceived)
        assert event.aggregate_id == aggregate_id
        assert event.payload["amount"] == "250.00"
        assert event.payload["currency"] == "EUR"
        assert event.payload["donor_id"] == str(donor_id)

    def test_create_donation_received_without_donor(self) -> None:
        event = create_donation_received(
            aggregate_id=uuid4(),
            amount="50.00",
            currency="PYG",
        )
        assert event.payload["donor_id"] is None
        assert event.actor_id is None
