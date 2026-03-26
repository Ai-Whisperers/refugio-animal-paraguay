"""Unit tests for Campaign Pydantic schemas."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from src.db.models.campaign import CampaignStatus, FundCategory
from src.db.models.donation import CurrencyCode
from src.schemas.campaign import (
    CampaignCreate,
    CampaignListResponse,
    CampaignPublicResponse,
    CampaignUpdate,
)

# ---------------------------------------------------------------------------
# CampaignCreate
# ---------------------------------------------------------------------------


class TestCampaignCreate:
    """Tests for CampaignCreate schema validation."""

    def test_valid_minimal_campaign(self) -> None:
        data = CampaignCreate(
            title="Medical Fund",
            description="Help us cover vet costs",
            target_amount_cents=100000,
        )
        assert data.title == "Medical Fund"
        assert data.currency == CurrencyCode.EUR
        assert data.fund_category == FundCategory.GENERAL
        assert data.allow_overfunding is True
        assert data.min_donation_cents is None
        assert data.max_donation_cents is None

    def test_valid_full_campaign(self) -> None:
        data = CampaignCreate(
            title="Rescue Campaign",
            description="Emergency rescue operations for stray animals",
            impact_story="Last month we rescued 15 dogs from the streets.",
            target_amount_cents=500000,
            currency=CurrencyCode.PYG,
            fund_category=FundCategory.RESCUE,
            image_url="https://example.com/rescue.jpg",
            deadline=datetime(2026, 6, 1, tzinfo=UTC),
            min_donation_cents=50000,
            max_donation_cents=5000000,
            allow_overfunding=False,
        )
        assert data.fund_category == FundCategory.RESCUE
        assert data.currency == CurrencyCode.PYG
        assert data.allow_overfunding is False

    def test_rejects_empty_title(self) -> None:
        with pytest.raises(ValidationError, match="title"):
            CampaignCreate(
                title="",
                description="Valid description",
                target_amount_cents=10000,
            )

    def test_rejects_empty_description(self) -> None:
        with pytest.raises(ValidationError, match="description"):
            CampaignCreate(
                title="Valid Title",
                description="",
                target_amount_cents=10000,
            )

    def test_rejects_zero_target_amount(self) -> None:
        with pytest.raises(ValidationError, match="target_amount_cents"):
            CampaignCreate(
                title="Valid Title",
                description="Valid description",
                target_amount_cents=0,
            )

    def test_rejects_negative_target_amount(self) -> None:
        with pytest.raises(ValidationError, match="target_amount_cents"):
            CampaignCreate(
                title="Valid Title",
                description="Valid description",
                target_amount_cents=-1000,
            )

    def test_rejects_zero_min_donation(self) -> None:
        with pytest.raises(ValidationError, match="min_donation_cents"):
            CampaignCreate(
                title="Valid Title",
                description="Valid description",
                target_amount_cents=10000,
                min_donation_cents=0,
            )

    def test_rejects_title_too_long(self) -> None:
        with pytest.raises(ValidationError, match="title"):
            CampaignCreate(
                title="X" * 256,
                description="Valid description",
                target_amount_cents=10000,
            )


# ---------------------------------------------------------------------------
# CampaignUpdate
# ---------------------------------------------------------------------------


class TestCampaignUpdate:
    """Tests for CampaignUpdate schema validation."""

    def test_valid_partial_update(self) -> None:
        data = CampaignUpdate(title="Updated Title")
        assert data.title == "Updated Title"
        assert data.description is None
        assert data.status is None

    def test_valid_status_update(self) -> None:
        data = CampaignUpdate(status=CampaignStatus.COMPLETED)
        assert data.status == CampaignStatus.COMPLETED

    def test_valid_empty_update(self) -> None:
        data = CampaignUpdate()
        assert data.title is None
        assert data.status is None

    def test_rejects_empty_title_string(self) -> None:
        with pytest.raises(ValidationError, match="title"):
            CampaignUpdate(title="")

    def test_rejects_invalid_target_amount(self) -> None:
        with pytest.raises(ValidationError, match="target_amount_cents"):
            CampaignUpdate(target_amount_cents=0)


# ---------------------------------------------------------------------------
# CampaignPublicResponse
# ---------------------------------------------------------------------------


class TestCampaignPublicResponse:
    """Tests for CampaignPublicResponse schema."""

    def _make_public_response(self, **overrides: object) -> dict:
        defaults: dict = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "Medical Fund",
            "description": "Help us cover vet costs",
            "impact_story": None,
            "target_amount_cents": 100000,
            "raised_amount_cents": 50000,
            "currency": "EUR",
            "fund_category": "medical",
            "status": "active",
            "image_url": None,
            "deadline": None,
            "min_donation_cents": None,
            "max_donation_cents": None,
            "allow_overfunding": True,
            "donation_count": 10,
            "progress_percentage": 50.0,
            "created_at": "2026-01-01T00:00:00Z",
        }
        defaults.update(overrides)
        return defaults

    def test_valid_public_response(self) -> None:
        data = CampaignPublicResponse(**self._make_public_response())
        assert data.raised_amount_cents == 50000
        assert data.donation_count == 10
        assert data.progress_percentage == 50.0

    def test_progress_percentage_can_exceed_100(self) -> None:
        data = CampaignPublicResponse(**self._make_public_response(progress_percentage=150.0))
        assert data.progress_percentage == 150.0

    def test_zero_donations(self) -> None:
        data = CampaignPublicResponse(
            **self._make_public_response(
                raised_amount_cents=0,
                donation_count=0,
                progress_percentage=0.0,
            )
        )
        assert data.donation_count == 0
        assert data.raised_amount_cents == 0


# ---------------------------------------------------------------------------
# CampaignListResponse
# ---------------------------------------------------------------------------


class TestCampaignListResponse:
    """Tests for CampaignListResponse pagination schema."""

    def test_valid_list_response(self) -> None:
        data = CampaignListResponse(
            items=[],
            total=0,
            page=1,
            page_size=20,
        )
        assert data.total == 0
        assert data.items == []

    def test_list_response_with_items(self) -> None:
        item = CampaignPublicResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            title="Test",
            description="Test desc",
            impact_story=None,
            target_amount_cents=10000,
            raised_amount_cents=0,
            currency="EUR",
            fund_category="general",
            status="active",
            image_url=None,
            deadline=None,
            min_donation_cents=None,
            max_donation_cents=None,
            allow_overfunding=True,
            donation_count=0,
            progress_percentage=0.0,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        data = CampaignListResponse(
            items=[item],
            total=1,
            page=1,
            page_size=20,
        )
        assert len(data.items) == 1
        assert data.total == 1
