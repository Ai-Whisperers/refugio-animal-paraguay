"""Unit tests for email template rendering.

Tests cover:
  - Template existence checks
  - Correct rendering with context variables
  - Missing template raises TemplateNotFound
  - Template variable substitution
"""

import pytest
from jinja2 import TemplateNotFound
from src.notifications.templates import TemplateRenderer


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------
@pytest.fixture
def renderer() -> TemplateRenderer:
    """TemplateRenderer using the project's real templates directory."""
    return TemplateRenderer()


# ---------------------------------------------------------------------------
# Template Existence
# ---------------------------------------------------------------------------
class TestTemplateExistence:
    """Verify all expected templates are present."""

    def test_base_template_exists(self, renderer: TemplateRenderer) -> None:
        assert renderer.has_template("base") is True

    def test_adoption_status_changed_exists(self, renderer: TemplateRenderer) -> None:
        assert renderer.has_template("adoption_status_changed") is True

    def test_donation_received_exists(self, renderer: TemplateRenderer) -> None:
        assert renderer.has_template("donation_received") is True

    def test_welcome_exists(self, renderer: TemplateRenderer) -> None:
        assert renderer.has_template("welcome") is True

    def test_nonexistent_template_returns_false(self, renderer: TemplateRenderer) -> None:
        assert renderer.has_template("nonexistent_template") is False


# ---------------------------------------------------------------------------
# Adoption Status Changed Template
# ---------------------------------------------------------------------------
class TestAdoptionStatusChangedTemplate:
    """Test the adoption_status_changed email template."""

    def test_renders_adopter_name(self, renderer: TemplateRenderer) -> None:
        html = renderer.render(
            "adoption_status_changed",
            {
                "adopter_name": "Maria Garcia",
                "animal_name": "Luna",
                "old_status": "pending",
                "new_status": "approved",
            },
        )
        assert "Maria Garcia" in html

    def test_renders_animal_name(self, renderer: TemplateRenderer) -> None:
        html = renderer.render(
            "adoption_status_changed",
            {
                "adopter_name": "Maria",
                "animal_name": "Luna",
                "old_status": "pending",
                "new_status": "approved",
            },
        )
        assert "Luna" in html

    def test_approved_includes_congratulations(self, renderer: TemplateRenderer) -> None:
        html = renderer.render(
            "adoption_status_changed",
            {
                "adopter_name": "Maria",
                "animal_name": "Luna",
                "old_status": "pending",
                "new_status": "approved",
            },
        )
        assert "Congratulations" in html

    def test_rejected_includes_regret_message(self, renderer: TemplateRenderer) -> None:
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

    def test_under_review_includes_review_message(self, renderer: TemplateRenderer) -> None:
        html = renderer.render(
            "adoption_status_changed",
            {
                "adopter_name": "Maria",
                "animal_name": "Luna",
                "old_status": "pending",
                "new_status": "under_review",
            },
        )
        assert "reviewed" in html

    def test_renders_status_values(self, renderer: TemplateRenderer) -> None:
        html = renderer.render(
            "adoption_status_changed",
            {
                "adopter_name": "Maria",
                "animal_name": "Luna",
                "old_status": "pending",
                "new_status": "approved",
            },
        )
        assert "Pending" in html
        assert "Approved" in html


# ---------------------------------------------------------------------------
# Donation Received Template
# ---------------------------------------------------------------------------
class TestDonationReceivedTemplate:
    """Test the donation_received email template."""

    def test_renders_donor_name(self, renderer: TemplateRenderer) -> None:
        html = renderer.render(
            "donation_received",
            {"donor_name": "Jan de Vries", "amount": "50.00", "currency": "EUR"},
        )
        assert "Jan de Vries" in html

    def test_renders_amount_and_currency(self, renderer: TemplateRenderer) -> None:
        html = renderer.render(
            "donation_received",
            {"donor_name": "Jan", "amount": "100.00", "currency": "EUR"},
        )
        assert "100.00" in html
        assert "EUR" in html

    def test_renders_receipt_number_when_present(self, renderer: TemplateRenderer) -> None:
        html = renderer.render(
            "donation_received",
            {
                "donor_name": "Jan",
                "amount": "50.00",
                "currency": "EUR",
                "receipt_number": "RCP-12345",
            },
        )
        assert "RCP-12345" in html

    def test_omits_receipt_when_absent(self, renderer: TemplateRenderer) -> None:
        html = renderer.render(
            "donation_received",
            {"donor_name": "Jan", "amount": "50.00", "currency": "EUR"},
        )
        assert "Receipt number" not in html


# ---------------------------------------------------------------------------
# Welcome Template
# ---------------------------------------------------------------------------
class TestWelcomeTemplate:
    """Test the welcome email template."""

    def test_renders_user_name(self, renderer: TemplateRenderer) -> None:
        html = renderer.render("welcome", {"user_name": "Carlos"})
        assert "Carlos" in html

    def test_includes_feature_list(self, renderer: TemplateRenderer) -> None:
        html = renderer.render("welcome", {"user_name": "Carlos"})
        assert "adoption" in html.lower()
        assert "donation" in html.lower()


# ---------------------------------------------------------------------------
# Error Handling
# ---------------------------------------------------------------------------
class TestTemplateErrors:
    """Verify error behavior for missing templates."""

    def test_render_missing_template_raises(self, renderer: TemplateRenderer) -> None:
        with pytest.raises(TemplateNotFound):
            renderer.render("this_template_does_not_exist")
