"""Unit tests for Campaign Pydantic schemas and helper functions."""

from datetime import UTC, datetime, timedelta

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
        assert data.featured is False
        assert data.photo_urls == []

    def test_valid_full_campaign(self) -> None:
        data = CampaignCreate(
            title="Rescue Campaign",
            description="Emergency rescue operations for stray animals",
            impact_story="Last month we rescued 15 dogs from the streets.",
            target_amount_cents=500000,
            currency=CurrencyCode.PYG,
            fund_category=FundCategory.RESCUE,
            featured=True,
            image_url="https://example.com/rescue.jpg",
            photo_urls=["https://example.com/photo1.jpg", "https://example.com/photo2.jpg"],
            deadline=datetime(2026, 6, 1, tzinfo=UTC),
            min_donation_cents=50000,
            max_donation_cents=5000000,
            allow_overfunding=False,
        )
        assert data.fund_category == FundCategory.RESCUE
        assert data.currency == CurrencyCode.PYG
        assert data.allow_overfunding is False
        assert data.featured is True
        assert len(data.photo_urls) == 2

    def test_valid_featured_default_false(self) -> None:
        data = CampaignCreate(
            title="Test",
            description="Test desc",
            target_amount_cents=10000,
        )
        assert data.featured is False

    def test_valid_photo_urls_empty_by_default(self) -> None:
        data = CampaignCreate(
            title="Test",
            description="Test desc",
            target_amount_cents=10000,
        )
        assert data.photo_urls == []

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

    def test_valid_status_update_completed(self) -> None:
        data = CampaignUpdate(status=CampaignStatus.COMPLETED)
        assert data.status == CampaignStatus.COMPLETED

    def test_valid_status_update_paused(self) -> None:
        data = CampaignUpdate(status=CampaignStatus.PAUSED)
        assert data.status == CampaignStatus.PAUSED

    def test_valid_status_update_archived(self) -> None:
        data = CampaignUpdate(status=CampaignStatus.ARCHIVED)
        assert data.status == CampaignStatus.ARCHIVED

    def test_valid_featured_update_true(self) -> None:
        data = CampaignUpdate(featured=True)
        assert data.featured is True

    def test_valid_featured_update_false(self) -> None:
        data = CampaignUpdate(featured=False)
        assert data.featured is False

    def test_valid_photo_urls_update(self) -> None:
        data = CampaignUpdate(photo_urls=["https://example.com/new.jpg"])
        assert data.photo_urls == ["https://example.com/new.jpg"]

    def test_valid_empty_update(self) -> None:
        data = CampaignUpdate()
        assert data.title is None
        assert data.status is None
        assert data.featured is None
        assert data.photo_urls is None

    def test_rejects_empty_title_string(self) -> None:
        with pytest.raises(ValidationError, match="title"):
            CampaignUpdate(title="")

    def test_rejects_invalid_target_amount(self) -> None:
        with pytest.raises(ValidationError, match="target_amount_cents"):
            CampaignUpdate(target_amount_cents=0)


# ---------------------------------------------------------------------------
# CampaignStatus lifecycle transitions
# ---------------------------------------------------------------------------


class TestCampaignStatusValues:
    """Tests that all required status values exist on the enum."""

    def test_draft_status_exists(self) -> None:
        assert CampaignStatus.DRAFT.value == "draft"

    def test_active_status_exists(self) -> None:
        assert CampaignStatus.ACTIVE.value == "active"

    def test_paused_status_exists(self) -> None:
        assert CampaignStatus.PAUSED.value == "paused"

    def test_completed_status_exists(self) -> None:
        assert CampaignStatus.COMPLETED.value == "completed"

    def test_archived_status_exists(self) -> None:
        assert CampaignStatus.ARCHIVED.value == "archived"

    def test_cancelled_status_exists_for_compat(self) -> None:
        assert CampaignStatus.CANCELLED.value == "cancelled"

    def test_all_statuses_accepted_in_update(self) -> None:
        for s in CampaignStatus:
            data = CampaignUpdate(status=s)
            assert data.status == s


# ---------------------------------------------------------------------------
# _compute_days_remaining (via CampaignPublicResponse)
# ---------------------------------------------------------------------------


class TestDaysRemaining:
    """Tests for the days_remaining computed field in CampaignPublicResponse."""

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
            "featured": False,
            "image_url": None,
            "photo_urls": [],
            "deadline": None,
            "days_remaining": None,
            "min_donation_cents": None,
            "max_donation_cents": None,
            "allow_overfunding": True,
            "donation_count": 10,
            "progress_percentage": 50.0,
            "created_at": "2026-01-01T00:00:00Z",
        }
        defaults.update(overrides)
        return defaults

    def test_no_deadline_returns_none(self) -> None:
        data = CampaignPublicResponse(**self._make_public_response())
        assert data.days_remaining is None
        assert data.deadline is None

    def test_future_deadline_returns_positive_days(self) -> None:
        future = datetime.now(tz=UTC) + timedelta(days=30)
        data = CampaignPublicResponse(
            **self._make_public_response(
                deadline=future.isoformat(),
                days_remaining=30,
            )
        )
        assert data.days_remaining == 30

    def test_past_deadline_can_be_zero(self) -> None:
        data = CampaignPublicResponse(
            **self._make_public_response(
                deadline="2020-01-01T00:00:00Z",
                days_remaining=0,
            )
        )
        assert data.days_remaining == 0

    def test_featured_flag_present(self) -> None:
        data = CampaignPublicResponse(**self._make_public_response(featured=True))
        assert data.featured is True

    def test_photo_urls_present(self) -> None:
        photos = ["https://example.com/a.jpg", "https://example.com/b.jpg"]
        data = CampaignPublicResponse(**self._make_public_response(photo_urls=photos))
        assert data.photo_urls == photos


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
            "featured": False,
            "image_url": None,
            "photo_urls": [],
            "deadline": None,
            "days_remaining": None,
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
        assert data.featured is False
        assert data.photo_urls == []
        assert data.days_remaining is None

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

    def test_paused_status_accepted(self) -> None:
        data = CampaignPublicResponse(**self._make_public_response(status="paused"))
        assert data.status == CampaignStatus.PAUSED

    def test_archived_status_accepted(self) -> None:
        data = CampaignPublicResponse(**self._make_public_response(status="archived"))
        assert data.status == CampaignStatus.ARCHIVED


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
            featured=False,
            image_url=None,
            photo_urls=[],
            deadline=None,
            days_remaining=None,
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
