"""Unit tests for src/schemas/adoption_request.py."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.db.models.adoption_request import AdoptionRequestStatus
from src.schemas.adoption_request import (
    AdoptionRequestCreate,
    AdoptionRequestResponse,
    AdoptionRequestStatusUpdate,
)


class TestAdoptionRequestCreate:
    def test_minimal_valid_payload(self) -> None:
        animal_id = uuid4()
        adopter_id = uuid4()
        req = AdoptionRequestCreate(animal_id=animal_id, adopter_id=adopter_id)
        assert req.animal_id == animal_id
        assert req.adopter_id == adopter_id
        assert req.notes is None

    def test_with_notes(self) -> None:
        req = AdoptionRequestCreate(
            animal_id=uuid4(),
            adopter_id=uuid4(),
            notes="Large yard, experienced owner",
        )
        assert req.notes == "Large yard, experienced owner"

    def test_missing_animal_id_raises(self) -> None:
        with pytest.raises(ValidationError):
            AdoptionRequestCreate(adopter_id=uuid4())  # type: ignore[call-arg]

    def test_missing_adopter_id_raises(self) -> None:
        with pytest.raises(ValidationError):
            AdoptionRequestCreate(animal_id=uuid4())  # type: ignore[call-arg]

    def test_invalid_uuid_raises(self) -> None:
        with pytest.raises(ValidationError):
            AdoptionRequestCreate(
                animal_id="not-a-uuid",  # type: ignore[arg-type]
                adopter_id=uuid4(),
            )


class TestAdoptionRequestStatusUpdate:
    def test_valid_pending(self) -> None:
        u = AdoptionRequestStatusUpdate(status=AdoptionRequestStatus.PENDING)
        assert u.status == AdoptionRequestStatus.PENDING

    def test_valid_approved(self) -> None:
        u = AdoptionRequestStatusUpdate(status=AdoptionRequestStatus.APPROVED)
        assert u.status == AdoptionRequestStatus.APPROVED

    def test_valid_rejected(self) -> None:
        u = AdoptionRequestStatusUpdate(status=AdoptionRequestStatus.REJECTED)
        assert u.status == AdoptionRequestStatus.REJECTED

    def test_valid_cancelled(self) -> None:
        u = AdoptionRequestStatusUpdate(status=AdoptionRequestStatus.CANCELLED)
        assert u.status == AdoptionRequestStatus.CANCELLED

    def test_invalid_status_raises(self) -> None:
        with pytest.raises(ValidationError):
            AdoptionRequestStatusUpdate(status="unknown")  # type: ignore[arg-type]


class TestAdoptionRequestResponse:
    def test_from_orm_attributes(self) -> None:
        now = datetime.now(timezone.utc)
        uid = uuid4()
        _animal_id = uuid4()
        _adopter_id = uuid4()

        class _FakeRequest:
            id = uid
            animal_id = _animal_id
            adopter_id = _adopter_id
            status = "pending"
            submitted_at = now
            decided_at = None
            notes = None
            created_at = now
            updated_at = now

        resp = AdoptionRequestResponse.model_validate(_FakeRequest())
        assert resp.id == uid
        assert resp.status == AdoptionRequestStatus.PENDING
        assert resp.decided_at is None

    def test_approved_status_from_orm(self) -> None:
        now = datetime.now(timezone.utc)

        class _FakeRequest:
            id = uuid4()
            animal_id = uuid4()
            adopter_id = uuid4()
            status = "approved"
            submitted_at = now
            decided_at = now
            notes = "Looks good"
            created_at = now
            updated_at = now

        resp = AdoptionRequestResponse.model_validate(_FakeRequest())
        assert resp.status == AdoptionRequestStatus.APPROVED
        assert resp.decided_at is not None
        assert resp.notes == "Looks good"
