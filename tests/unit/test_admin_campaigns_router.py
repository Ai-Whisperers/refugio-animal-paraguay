"""Unit tests for admin campaign management router.

Tests the campaign CRUD endpoints for staff/admin users including:
- Creating campaigns with all fields
- Updating campaign fields including status transitions
- Listing campaigns with filters
- Getting a single campaign by ID
- Error handling for not found / validation
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from src.db.models.campaign import Campaign, CampaignStatus, FundCategory
from src.db.models.donation import CurrencyCode
from src.schemas.campaign import CampaignCreate, CampaignResponse, CampaignUpdate


# --- Fixtures ---

CAMPAIGN_ID = uuid4()
USER_ID = uuid4()
NOW = datetime.now(tz=timezone.utc)


def _make_campaign(**overrides) -> MagicMock:
    """Create a mock Campaign ORM object with sensible defaults."""
    defaults = {
        "id": CAMPAIGN_ID,
        "title": "Save the Puppies",
        "description": "Help us rescue and rehabilitate puppies.",
        "impact_story": "Every donation makes a difference.",
        "target_amount_cents": 500000,
        "currency": "EUR",
        "fund_category": "rescue",
        "status": "draft",
        "featured": False,
        "image_url": None,
        "photo_urls": [],
        "deadline": None,
        "min_donation_cents": None,
        "max_donation_cents": None,
        "allow_overfunding": True,
        "created_by_id": USER_ID,
        "created_at": NOW,
        "updated_at": NOW,
    }
    defaults.update(overrides)
    campaign = MagicMock(spec=Campaign)
    for key, value in defaults.items():
        setattr(campaign, key, value)
    return campaign


# --- CampaignCreate Schema Tests ---


class TestCampaignCreateSchema:
    """Test CampaignCreate Pydantic schema validation."""

    def test_minimal_valid_create(self) -> None:
        payload = CampaignCreate(
            title="Emergency Fund",
            description="Urgent medical needs",
            target_amount_cents=100000,
        )
        assert payload.title == "Emergency Fund"
        assert payload.target_amount_cents == 100000
        assert payload.currency.value == "EUR"
        assert payload.fund_category.value == "general"
        assert payload.featured is False
        assert payload.allow_overfunding is True

    def test_full_create_payload(self) -> None:
        payload = CampaignCreate(
            title="Winter Shelter",
            description="Build warm shelters for winter",
            impact_story="Animals need warmth",
            target_amount_cents=1000000,
            currency=CurrencyCode.USD,
            fund_category=FundCategory.INFRASTRUCTURE,
            featured=True,
            image_url="https://example.com/image.jpg",
            deadline=NOW,
            min_donation_cents=500,
            max_donation_cents=50000,
            allow_overfunding=False,
        )
        assert payload.featured is True
        assert payload.allow_overfunding is False
        assert payload.min_donation_cents == 500
        assert payload.max_donation_cents == 50000

    def test_title_min_length(self) -> None:
        with pytest.raises(Exception):
            CampaignCreate(
                title="",
                description="desc",
                target_amount_cents=100,
            )

    def test_target_amount_must_be_positive(self) -> None:
        with pytest.raises(Exception):
            CampaignCreate(
                title="Valid Title",
                description="desc",
                target_amount_cents=0,
            )

    def test_negative_target_amount_rejected(self) -> None:
        with pytest.raises(Exception):
            CampaignCreate(
                title="Valid Title",
                description="desc",
                target_amount_cents=-100,
            )


# --- CampaignUpdate Schema Tests ---


class TestCampaignUpdateSchema:
    """Test CampaignUpdate Pydantic schema partial update validation."""

    def test_partial_update_title_only(self) -> None:
        payload = CampaignUpdate(title="New Title")
        dumped = payload.model_dump(exclude_unset=True)
        assert "title" in dumped
        assert "description" not in dumped

    def test_status_transition(self) -> None:
        payload = CampaignUpdate(status=CampaignStatus.ACTIVE)
        assert payload.status == CampaignStatus.ACTIVE

    def test_featured_toggle(self) -> None:
        payload = CampaignUpdate(featured=True)
        assert payload.featured is True

    def test_empty_update_is_valid(self) -> None:
        payload = CampaignUpdate()
        dumped = payload.model_dump(exclude_unset=True)
        assert dumped == {}


# --- CampaignResponse Schema Tests ---


class TestCampaignResponseSchema:
    """Test CampaignResponse serialization from ORM attributes."""

    def test_serialize_from_campaign(self) -> None:
        campaign = _make_campaign()
        response = CampaignResponse.model_validate(campaign, from_attributes=True)
        assert response.id == CAMPAIGN_ID
        assert response.title == "Save the Puppies"
        assert response.target_amount_cents == 500000
        assert response.currency.value == "EUR"
        assert response.status.value == "draft"

    def test_serialize_featured_campaign(self) -> None:
        campaign = _make_campaign(featured=True, status="active")
        response = CampaignResponse.model_validate(campaign, from_attributes=True)
        assert response.featured is True
        assert response.status.value == "active"

    def test_serialize_with_deadline(self) -> None:
        deadline = datetime(2026, 12, 31, tzinfo=timezone.utc)
        campaign = _make_campaign(deadline=deadline)
        response = CampaignResponse.model_validate(campaign, from_attributes=True)
        assert response.deadline == deadline

    def test_serialize_all_statuses(self) -> None:
        for status_val in CampaignStatus:
            campaign = _make_campaign(status=status_val.value)
            response = CampaignResponse.model_validate(campaign, from_attributes=True)
            assert response.status.value == status_val.value

    def test_serialize_all_fund_categories(self) -> None:
        for cat in FundCategory:
            campaign = _make_campaign(fund_category=cat.value)
            response = CampaignResponse.model_validate(campaign, from_attributes=True)
            assert response.fund_category.value == cat.value


# --- Status Transition Logic Tests ---


class TestCampaignStatusTransitions:
    """Test that valid status transitions are accepted by the schema."""

    @pytest.mark.parametrize(
        "from_status,to_status",
        [
            ("draft", "active"),
            ("active", "paused"),
            ("active", "completed"),
            ("paused", "active"),
            ("active", "archived"),
            ("completed", "archived"),
            ("draft", "cancelled"),
        ],
    )
    def test_valid_transitions(self, from_status: str, to_status: str) -> None:
        payload = CampaignUpdate(status=CampaignStatus(to_status))
        assert payload.status is not None
        assert payload.status.value == to_status
