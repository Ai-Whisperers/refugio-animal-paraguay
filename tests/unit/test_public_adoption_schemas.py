"""Unit tests for public adoption application schemas."""

import uuid

import pytest
from pydantic import ValidationError
from src.schemas.public_adoption import (
    PublicAdoptionApplicationCreate,
    PublicAdoptionApplicationResponse,
)


class TestPublicAdoptionApplicationCreate:
    """Tests for the public adoption application create schema."""

    def test_valid_application(self) -> None:
        app = PublicAdoptionApplicationCreate(
            animal_id=uuid.uuid4(),
            full_name="Maria Garcia",
            email="maria@example.com",
            phone="+595981123456",
            message="I would love to adopt this dog.",
            gdpr_consent=True,
        )
        assert app.full_name == "Maria Garcia"
        assert app.gdpr_consent is True

    def test_minimal_application(self) -> None:
        app = PublicAdoptionApplicationCreate(
            animal_id=uuid.uuid4(),
            full_name="Juan",
            email="juan@example.com",
            gdpr_consent=True,
        )
        assert app.phone is None
        assert app.message is None

    def test_missing_required_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            PublicAdoptionApplicationCreate(
                animal_id=uuid.uuid4(),
                email="test@example.com",
                gdpr_consent=True,
            )

    def test_missing_required_email_raises(self) -> None:
        with pytest.raises(ValidationError):
            PublicAdoptionApplicationCreate(
                animal_id=uuid.uuid4(),
                full_name="Test",
                gdpr_consent=True,
            )

    def test_invalid_email_raises(self) -> None:
        with pytest.raises(ValidationError):
            PublicAdoptionApplicationCreate(
                animal_id=uuid.uuid4(),
                full_name="Test",
                email="not-an-email",
                gdpr_consent=True,
            )

    def test_missing_gdpr_consent_raises(self) -> None:
        with pytest.raises(ValidationError):
            PublicAdoptionApplicationCreate(
                animal_id=uuid.uuid4(),
                full_name="Test",
                email="test@example.com",
            )

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            PublicAdoptionApplicationCreate(
                animal_id=uuid.uuid4(),
                full_name="",
                email="test@example.com",
                gdpr_consent=True,
            )

    def test_message_too_long_raises(self) -> None:
        with pytest.raises(ValidationError):
            PublicAdoptionApplicationCreate(
                animal_id=uuid.uuid4(),
                full_name="Test",
                email="test@example.com",
                gdpr_consent=True,
                message="x" * 2001,
            )

    def test_message_at_max_length(self) -> None:
        app = PublicAdoptionApplicationCreate(
            animal_id=uuid.uuid4(),
            full_name="Test",
            email="test@example.com",
            gdpr_consent=True,
            message="x" * 2000,
        )
        assert len(app.message) == 2000


class TestPublicAdoptionApplicationResponse:
    """Tests for the public adoption application response schema."""

    def test_response_shape(self) -> None:
        resp = PublicAdoptionApplicationResponse(
            id=uuid.uuid4(),
            animal_id=uuid.uuid4(),
            status="pending",
            submitted_at="2026-03-26T12:00:00Z",
        )
        assert resp.status == "pending"
        assert resp.message == "Your adoption application has been submitted successfully."
