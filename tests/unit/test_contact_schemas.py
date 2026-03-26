"""Unit tests for contact and inquiry form schemas."""

import pytest
from pydantic import ValidationError
from src.schemas.contact import (
    AnimalInquiryCreate,
    ContactFormCreate,
    ContactSubmissionResponse,
)


class TestContactFormCreate:
    """Tests for the general contact form create schema."""

    def test_valid_contact_form(self) -> None:
        form = ContactFormCreate(
            visitor_name="Maria Garcia",
            visitor_email="maria@example.com",
            subject="Adoption inquiry",
            message="I would like to know more about your adoption process.",
        )
        assert form.visitor_name == "Maria Garcia"
        assert form.subject == "Adoption inquiry"

    def test_name_too_short_raises(self) -> None:
        with pytest.raises(ValidationError):
            ContactFormCreate(
                visitor_name="AB",
                visitor_email="test@example.com",
                subject="Valid subject line",
                message="This is a valid message body.",
            )

    def test_name_too_long_raises(self) -> None:
        with pytest.raises(ValidationError):
            ContactFormCreate(
                visitor_name="x" * 101,
                visitor_email="test@example.com",
                subject="Valid subject line",
                message="This is a valid message body.",
            )

    def test_invalid_email_raises(self) -> None:
        with pytest.raises(ValidationError):
            ContactFormCreate(
                visitor_name="Test User",
                visitor_email="not-an-email",
                subject="Valid subject line",
                message="This is a valid message body.",
            )

    def test_subject_too_short_raises(self) -> None:
        with pytest.raises(ValidationError):
            ContactFormCreate(
                visitor_name="Test User",
                visitor_email="test@example.com",
                subject="Short",
                message="This is a valid message body.",
            )

    def test_subject_too_long_raises(self) -> None:
        with pytest.raises(ValidationError):
            ContactFormCreate(
                visitor_name="Test User",
                visitor_email="test@example.com",
                subject="x" * 201,
                message="This is a valid message body.",
            )

    def test_message_too_short_raises(self) -> None:
        with pytest.raises(ValidationError):
            ContactFormCreate(
                visitor_name="Test User",
                visitor_email="test@example.com",
                subject="Valid subject line",
                message="Too short",
            )

    def test_message_too_long_raises(self) -> None:
        with pytest.raises(ValidationError):
            ContactFormCreate(
                visitor_name="Test User",
                visitor_email="test@example.com",
                subject="Valid subject line",
                message="x" * 5001,
            )

    def test_message_at_max_length(self) -> None:
        form = ContactFormCreate(
            visitor_name="Test User",
            visitor_email="test@example.com",
            subject="Valid subject line",
            message="x" * 5000,
        )
        assert len(form.message) == 5000

    def test_missing_required_fields_raises(self) -> None:
        with pytest.raises(ValidationError):
            ContactFormCreate(
                visitor_name="Test User",
                visitor_email="test@example.com",
            )


class TestAnimalInquiryCreate:
    """Tests for the animal inquiry create schema."""

    def test_valid_inquiry(self) -> None:
        inquiry = AnimalInquiryCreate(
            visitor_name="Juan Lopez",
            visitor_email="juan@example.com",
            message="I am interested in adopting this animal.",
        )
        assert inquiry.visitor_name == "Juan Lopez"

    def test_name_too_short_raises(self) -> None:
        with pytest.raises(ValidationError):
            AnimalInquiryCreate(
                visitor_name="AB",
                visitor_email="test@example.com",
                message="I am interested in adopting this animal.",
            )

    def test_message_too_short_raises(self) -> None:
        with pytest.raises(ValidationError):
            AnimalInquiryCreate(
                visitor_name="Test User",
                visitor_email="test@example.com",
                message="Too short",
            )

    def test_missing_email_raises(self) -> None:
        with pytest.raises(ValidationError):
            AnimalInquiryCreate(
                visitor_name="Test User",
                message="I am interested in adopting this animal.",
            )


class TestContactSubmissionResponse:
    """Tests for the submission response schema."""

    def test_response_shape(self) -> None:
        import uuid

        resp = ContactSubmissionResponse(
            id=uuid.uuid4(),
            form_type="general",
            submitted_at="2026-03-26T12:00:00Z",
        )
        assert resp.form_type == "general"
        assert "received" in resp.message
