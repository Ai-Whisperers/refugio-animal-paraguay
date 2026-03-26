"""Unit tests for adoption notification event publishing.

Tests that domain events are correctly created and published when
adoption requests are created or have their status changed.
"""

from __future__ import annotations

from uuid import uuid4

from src.events.domain_events import (
    AdoptionRequestCreated,
    create_adoption_request_created,
    create_adoption_status_changed,
)
from src.events.types import EventType


class TestAdoptionRequestCreatedEvent:
    """Tests for AdoptionRequestCreated domain event."""

    def test_event_has_correct_type(self) -> None:
        event = AdoptionRequestCreated(
            payload={"adopter_name": "Ana", "animal_name": "Luna"},
            aggregate_id=uuid4(),
        )
        assert event.event_type == EventType.ADOPTION_REQUEST_CREATED

    def test_event_has_correct_aggregate_type(self) -> None:
        event = AdoptionRequestCreated(
            payload={},
            aggregate_id=uuid4(),
        )
        assert event.aggregate_type == "adoption_request"

    def test_factory_creates_event_with_payload(self) -> None:
        req_id = uuid4()
        actor_id = uuid4()
        event = create_adoption_request_created(
            aggregate_id=req_id,
            adopter_name="Carlos",
            animal_name="Max",
            adopter_email="carlos@example.com",
            actor_id=actor_id,
        )
        assert event.event_type == EventType.ADOPTION_REQUEST_CREATED
        assert event.aggregate_id == req_id
        assert event.actor_id == actor_id
        assert event.payload["adopter_name"] == "Carlos"
        assert event.payload["animal_name"] == "Max"
        assert event.payload["adopter_email"] == "carlos@example.com"

    def test_factory_without_optional_fields(self) -> None:
        event = create_adoption_request_created(
            aggregate_id=uuid4(),
            adopter_name="Ana",
            animal_name="Luna",
        )
        assert event.payload["adopter_email"] is None
        assert event.actor_id is None


class TestAdoptionStatusChangedEvent:
    """Tests for AdoptionStatusChanged domain event factory."""

    def test_factory_creates_event_with_status_payload(self) -> None:
        req_id = uuid4()
        event = create_adoption_status_changed(
            aggregate_id=req_id,
            old_status="pending",
            new_status="approved",
            actor_id=uuid4(),
        )
        assert event.event_type == EventType.ADOPTION_STATUS_CHANGED
        assert event.aggregate_id == req_id
        assert event.payload["old_status"] == "pending"
        assert event.payload["new_status"] == "approved"

    def test_factory_without_actor_id(self) -> None:
        event = create_adoption_status_changed(
            aggregate_id=uuid4(),
            old_status="pending",
            new_status="rejected",
        )
        assert event.actor_id is None

    def test_event_has_unique_id(self) -> None:
        event1 = create_adoption_status_changed(
            aggregate_id=uuid4(),
            old_status="pending",
            new_status="approved",
        )
        event2 = create_adoption_status_changed(
            aggregate_id=uuid4(),
            old_status="pending",
            new_status="rejected",
        )
        assert event1.id != event2.id

    def test_event_has_idempotency_key(self) -> None:
        event = create_adoption_status_changed(
            aggregate_id=uuid4(),
            old_status="pending",
            new_status="approved",
        )
        assert event.idempotency_key is not None


class TestNotificationHandlerRegistration:
    """Tests for email notification handler event subscriptions."""

    def test_adoption_request_created_handler_exists(self) -> None:
        from src.notifications.handlers import NotificationHandlers

        assert hasattr(NotificationHandlers, "on_adoption_request_created")
        assert callable(NotificationHandlers.on_adoption_request_created)

    def test_adoption_status_changed_handler_exists(self) -> None:
        from src.notifications.handlers import NotificationHandlers

        assert hasattr(NotificationHandlers, "on_adoption_status_changed")

    def test_get_staff_emails_helper_exists(self) -> None:
        from src.notifications.handlers import NotificationHandlers

        assert hasattr(NotificationHandlers, "_get_staff_emails")
