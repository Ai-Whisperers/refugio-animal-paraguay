"""Unit tests for adoption status email enhancements (RAP-113).

Tests cover:
  - Event factory includes/excludes notes in payload
  - Template renders bilingual content for each status
  - Template renders staff notes when provided
  - Template omits staff notes block when absent
"""

from uuid import uuid4

import pytest
from src.events.domain_events import create_adoption_status_changed
from src.notifications.templates import TemplateRenderer


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------
@pytest.fixture
def renderer() -> TemplateRenderer:
    """TemplateRenderer using the project's real templates directory."""
    return TemplateRenderer()


# ---------------------------------------------------------------------------
# Event Factory — notes support
# ---------------------------------------------------------------------------
class TestAdoptionStatusChangedEventFactory:
    """Verify create_adoption_status_changed passes notes through payload."""

    def test_payload_includes_notes_when_provided(self) -> None:
        event = create_adoption_status_changed(
            aggregate_id=uuid4(),
            old_status="pending",
            new_status="approved",
            notes="Home visit completed successfully",
        )
        assert event.payload["notes"] == "Home visit completed successfully"

    def test_payload_excludes_notes_when_none(self) -> None:
        event = create_adoption_status_changed(
            aggregate_id=uuid4(),
            old_status="pending",
            new_status="rejected",
        )
        assert "notes" not in event.payload

    def test_payload_excludes_notes_when_empty_string(self) -> None:
        event = create_adoption_status_changed(
            aggregate_id=uuid4(),
            old_status="pending",
            new_status="rejected",
            notes="",
        )
        assert "notes" not in event.payload


# ---------------------------------------------------------------------------
# Email Template — bilingual + notes
# ---------------------------------------------------------------------------
class TestAdoptionStatusEmailTemplate:
    """Test the enhanced adoption_status_changed email template."""

    def test_approved_renders_bilingual_congratulations(self, renderer: TemplateRenderer) -> None:
        html = renderer.render(
            "adoption_status_changed",
            {
                "adopter_name": "Maria Garcia",
                "animal_name": "Luna",
                "old_status": "pending",
                "new_status": "approved",
            },
        )
        # Spanish
        assert "Felicitaciones" in html
        # English
        assert "Congratulations" in html

    def test_rejected_renders_bilingual_regret(self, renderer: TemplateRenderer) -> None:
        html = renderer.render(
            "adoption_status_changed",
            {
                "adopter_name": "Maria",
                "animal_name": "Luna",
                "old_status": "pending",
                "new_status": "rejected",
            },
        )
        assert "not approved" in html
        assert "no fue aprobada" in html

    def test_cancelled_renders_bilingual_message(self, renderer: TemplateRenderer) -> None:
        html = renderer.render(
            "adoption_status_changed",
            {
                "adopter_name": "Maria",
                "animal_name": "Luna",
                "old_status": "approved",
                "new_status": "cancelled",
            },
        )
        assert "cancelada" in html.lower()
        assert "cancelled" in html.lower()

    def test_renders_staff_notes_when_provided(self, renderer: TemplateRenderer) -> None:
        html = renderer.render(
            "adoption_status_changed",
            {
                "adopter_name": "Maria",
                "animal_name": "Luna",
                "old_status": "pending",
                "new_status": "approved",
                "staff_notes": "Home visit was excellent",
            },
        )
        assert "Home visit was excellent" in html
        assert "Notas del equipo" in html

    def test_omits_staff_notes_when_absent(self, renderer: TemplateRenderer) -> None:
        html = renderer.render(
            "adoption_status_changed",
            {
                "adopter_name": "Maria",
                "animal_name": "Luna",
                "old_status": "pending",
                "new_status": "approved",
            },
        )
        assert "Notas del equipo" not in html

    def test_omits_staff_notes_when_none(self, renderer: TemplateRenderer) -> None:
        html = renderer.render(
            "adoption_status_changed",
            {
                "adopter_name": "Maria",
                "animal_name": "Luna",
                "old_status": "pending",
                "new_status": "approved",
                "staff_notes": None,
            },
        )
        assert "Notas del equipo" not in html

    def test_renders_adopter_and_animal_names(self, renderer: TemplateRenderer) -> None:
        html = renderer.render(
            "adoption_status_changed",
            {
                "adopter_name": "Jan de Vries",
                "animal_name": "Rex",
                "old_status": "pending",
                "new_status": "approved",
            },
        )
        assert "Jan de Vries" in html
        assert "Rex" in html
