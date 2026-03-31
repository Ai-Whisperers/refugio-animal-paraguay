"""Unit tests for email template API router.

Tests schema validation and response shape for EmailTemplate endpoints.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from src.db.models.email_template import EmailTemplate, TemplateStatus
from src.schemas.email_template import (
    EmailTemplateCreate,
    EmailTemplateResponse,
    EmailTemplateSummary,
    EmailTemplateUpdate,
)

TEMPLATE_ID = uuid4()
USER_ID = uuid4()
NOW = datetime.now(tz=UTC)


def _make_template(**overrides) -> MagicMock:
    """Create a mock EmailTemplate ORM object with sensible defaults."""
    defaults = {
        "id": TEMPLATE_ID,
        "name": "Welcome Newsletter",
        "description": "Monthly welcome message",
        "subject": "Welcome to Refugio Animal Paraguay!",
        "html_body": "<html><body><h1>Welcome</h1></body></html>",
        "text_body": "Welcome to Refugio Animal Paraguay!",
        "status": TemplateStatus.DRAFT,
        "created_by_id": USER_ID,
        "created_at": NOW,
        "updated_at": NOW,
    }
    defaults.update(overrides)
    template = MagicMock(spec=EmailTemplate)
    for key, value in defaults.items():
        setattr(template, key, value)
    return template


class TestEmailTemplateCreateSchema:
    """Tests for EmailTemplateCreate schema validation."""

    def test_valid_create_succeeds(self):
        payload = EmailTemplateCreate(
            name="My Template",
            subject="Hello World",
            html_body="<p>Hello</p>",
        )
        assert payload.name == "My Template"
        assert payload.text_body is None
        assert payload.description is None

    def test_empty_name_fails(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            EmailTemplateCreate(name="", subject="s", html_body="<p></p>")

    def test_empty_subject_fails(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            EmailTemplateCreate(name="Name", subject="", html_body="<p></p>")

    def test_empty_html_body_fails(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            EmailTemplateCreate(name="Name", subject="Subject", html_body="")

    def test_subject_max_length(self):
        from pydantic import ValidationError

        long_subject = "a" * 501
        with pytest.raises(ValidationError):
            EmailTemplateCreate(name="Name", subject=long_subject, html_body="<p>x</p>")

    def test_with_all_fields(self):
        payload = EmailTemplateCreate(
            name="Full Template",
            description="My description",
            subject="Full subject",
            html_body="<html><body>Hello</body></html>",
            text_body="Hello",
        )
        assert payload.text_body == "Hello"
        assert payload.description == "My description"


class TestEmailTemplateUpdateSchema:
    """Tests for EmailTemplateUpdate schema validation."""

    def test_all_fields_optional(self):
        update = EmailTemplateUpdate()
        assert update.name is None
        assert update.subject is None
        assert update.html_body is None
        assert update.status is None

    def test_status_update(self):
        update = EmailTemplateUpdate(status=TemplateStatus.ACTIVE)
        assert update.status == TemplateStatus.ACTIVE

    def test_partial_update(self):
        update = EmailTemplateUpdate(name="Updated Name")
        assert update.name == "Updated Name"
        assert update.subject is None


class TestEmailTemplateResponseSchema:
    """Tests for EmailTemplateResponse schema serialisation."""

    def test_from_orm(self):
        template = _make_template()
        response = EmailTemplateResponse.model_validate(template)
        assert response.id == TEMPLATE_ID
        assert response.name == "Welcome Newsletter"
        assert response.status == TemplateStatus.DRAFT

    def test_summary_from_orm(self):
        template = _make_template()
        summary = EmailTemplateSummary.model_validate(template)
        assert summary.id == TEMPLATE_ID
        assert summary.name == "Welcome Newsletter"
        assert summary.subject == "Welcome to Refugio Animal Paraguay!"
        # Summary excludes html_body and text_body
        assert not hasattr(summary, "html_body")

    def test_archived_template(self):
        template = _make_template(status=TemplateStatus.ARCHIVED)
        response = EmailTemplateResponse.model_validate(template)
        assert response.status == TemplateStatus.ARCHIVED
