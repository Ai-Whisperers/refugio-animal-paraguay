"""Unit tests for DomainEvent base class and EventType enum."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from src.events.types import DomainEvent, EventType


class TestEventType:
    """Tests for the EventType enum."""

    def test_event_type_values_follow_dot_notation(self) -> None:
        for event_type in EventType:
            assert "." in event_type.value, f"{event_type.name} must use dot notation"

    def test_adoption_domain_events_exist(self) -> None:
        assert EventType.ADOPTION_STATUS_CHANGED == "adoption.status_changed"
        assert EventType.ADOPTION_REQUEST_CREATED == "adoption.request_created"

    def test_donation_domain_events_exist(self) -> None:
        assert EventType.DONATION_RECEIVED == "donation.received"
        assert EventType.DONATION_REFUNDED == "donation.refunded"

    def test_medical_domain_events_exist(self) -> None:
        assert EventType.MEDICAL_ALERT_CREATED == "medical.alert_created"
        assert EventType.MEDICAL_RECORD_ADDED == "medical.record_added"

    def test_volunteer_domain_events_exist(self) -> None:
        assert EventType.VOLUNTEER_SHIFT_CREATED == "volunteer.shift_created"
        assert EventType.VOLUNTEER_SHIFT_COMPLETED == "volunteer.shift_completed"

    def test_animal_domain_events_exist(self) -> None:
        assert EventType.ANIMAL_INTAKE_COMPLETED == "animal.intake_completed"
        assert EventType.ANIMAL_STATUS_CHANGED == "animal.status_changed"

    def test_event_type_is_string_enum(self) -> None:
        assert isinstance(EventType.ADOPTION_STATUS_CHANGED, str)

    def test_subscription_domain_events_exist(self) -> None:
        assert EventType.SUBSCRIPTION_PAYMENT_FAILED == "subscription.payment_failed"
        assert EventType.SUBSCRIPTION_CANCELLED_DUNNING == "subscription.cancelled_dunning"

    def test_event_type_count(self) -> None:
        assert len(EventType) == 12


class TestDomainEvent:
    """Tests for the DomainEvent base model."""

    def test_create_with_required_fields_only(self) -> None:
        event = DomainEvent(event_type=EventType.ADOPTION_STATUS_CHANGED)
        assert event.event_type == EventType.ADOPTION_STATUS_CHANGED
        assert isinstance(event.id, UUID)
        assert isinstance(event.idempotency_key, UUID)
        assert isinstance(event.timestamp, datetime)
        assert event.payload == {}
        assert event.actor_id is None
        assert event.aggregate_id is None
        assert event.aggregate_type is None

    def test_create_with_all_fields(self) -> None:
        event_id = uuid4()
        actor_id = uuid4()
        aggregate_id = uuid4()
        idem_key = uuid4()

        event = DomainEvent(
            id=event_id,
            event_type=EventType.DONATION_RECEIVED,
            payload={"amount": "100.00", "currency": "EUR"},
            actor_id=actor_id,
            idempotency_key=idem_key,
            aggregate_id=aggregate_id,
            aggregate_type="donation",
        )

        assert event.id == event_id
        assert event.event_type == EventType.DONATION_RECEIVED
        assert event.payload == {"amount": "100.00", "currency": "EUR"}
        assert event.actor_id == actor_id
        assert event.idempotency_key == idem_key
        assert event.aggregate_id == aggregate_id
        assert event.aggregate_type == "donation"

    def test_timestamp_is_utc(self) -> None:
        event = DomainEvent(event_type=EventType.ANIMAL_INTAKE_COMPLETED)
        assert event.timestamp.tzinfo == UTC

    def test_each_event_gets_unique_id(self) -> None:
        event_a = DomainEvent(event_type=EventType.ADOPTION_STATUS_CHANGED)
        event_b = DomainEvent(event_type=EventType.ADOPTION_STATUS_CHANGED)
        assert event_a.id != event_b.id

    def test_each_event_gets_unique_idempotency_key(self) -> None:
        event_a = DomainEvent(event_type=EventType.ADOPTION_STATUS_CHANGED)
        event_b = DomainEvent(event_type=EventType.ADOPTION_STATUS_CHANGED)
        assert event_a.idempotency_key != event_b.idempotency_key

    def test_event_is_frozen(self) -> None:
        event = DomainEvent(event_type=EventType.DONATION_RECEIVED)
        with pytest.raises(ValidationError):
            event.payload = {"changed": True}

    def test_event_serialization_roundtrip(self) -> None:
        event = DomainEvent(
            event_type=EventType.MEDICAL_ALERT_CREATED,
            payload={"severity": "high"},
            aggregate_type="medical_record",
        )
        data = event.model_dump()
        restored = DomainEvent.model_validate(data)
        assert restored.id == event.id
        assert restored.event_type == event.event_type
        assert restored.payload == event.payload
