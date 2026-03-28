"""Unit tests for community needs API and model."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.db.models.community_need import CommunityNeed, NeedCategory, NeedStatus

# --- Model tests ---


class TestCommunityNeedModel:
    """Tests for CommunityNeed ORM model."""

    def test_need_status_values(self) -> None:
        assert NeedStatus.OPEN == "open"
        assert NeedStatus.FULFILLED == "fulfilled"
        assert NeedStatus.CANCELLED == "cancelled"

    def test_need_category_values(self) -> None:
        assert NeedCategory.MEDICAL == "medical"
        assert NeedCategory.FOOD == "food"
        assert NeedCategory.SHELTER == "shelter"
        assert NeedCategory.TRANSPORT == "transport"
        assert NeedCategory.SUPPLIES == "supplies"
        assert NeedCategory.OTHER == "other"

    def test_all_categories_are_six(self) -> None:
        assert len(NeedCategory) == 6


# --- Response helper tests ---


class TestNeedResponse:
    """Tests for the _to_response helper."""

    def _make_need(self, **overrides: object) -> CommunityNeed:
        defaults = {
            "id": uuid4(),
            "title": "Alimento para 20 perros",
            "description": "Necesitamos 50kg de alimento",
            "category": NeedCategory.FOOD,
            "status": NeedStatus.OPEN,
            "estimated_cost_cents": 10000,
            "current_raised_cents": 5000,
            "currency": "USD",
            "donor_count": 3,
            "creator_id": uuid4(),
            "image_url": None,
            "created_at": datetime(2026, 3, 28, tzinfo=UTC),
            "updated_at": datetime(2026, 3, 28, tzinfo=UTC),
        }
        defaults.update(overrides)
        need = MagicMock(spec=CommunityNeed)
        for key, value in defaults.items():
            setattr(need, key, value)
        return need

    def test_progress_percent_calculation(self) -> None:
        from src.api.community_needs import _to_response

        need = self._make_need(estimated_cost_cents=10000, current_raised_cents=2500)
        response = _to_response(need)
        assert response.progress_percent == 25.0

    def test_progress_percent_zero_cost(self) -> None:
        from src.api.community_needs import _to_response

        need = self._make_need(estimated_cost_cents=0, current_raised_cents=0)
        # Avoid division by zero — should be 0%
        response = _to_response(need)
        assert response.progress_percent == 0.0

    def test_progress_percent_capped_at_100(self) -> None:
        from src.api.community_needs import _to_response

        need = self._make_need(estimated_cost_cents=5000, current_raised_cents=7500)
        response = _to_response(need)
        assert response.progress_percent == 100.0

    def test_progress_percent_full(self) -> None:
        from src.api.community_needs import _to_response

        need = self._make_need(estimated_cost_cents=10000, current_raised_cents=10000)
        response = _to_response(need)
        assert response.progress_percent == 100.0

    def test_response_includes_all_fields(self) -> None:
        from src.api.community_needs import _to_response

        need_id = uuid4()
        creator_id = uuid4()
        need = self._make_need(
            id=need_id,
            title="Test need",
            description="Test desc",
            category=NeedCategory.MEDICAL,
            status=NeedStatus.OPEN,
            estimated_cost_cents=5000,
            current_raised_cents=1000,
            currency="EUR",
            donor_count=2,
            creator_id=creator_id,
            image_url="https://example.com/img.jpg",
        )
        response = _to_response(need)
        assert response.id == need_id
        assert response.title == "Test need"
        assert response.category == "medical"
        assert response.currency == "EUR"
        assert response.donor_count == 2
        assert response.image_url == "https://example.com/img.jpg"
        assert response.progress_percent == 20.0


# --- Target validation tests ---


class TestNeedTargetValidation:
    """Tests for the need target validator."""

    @pytest.mark.asyncio
    async def test_validates_existing_open_need(self) -> None:
        from src.services.donation_target_service import _validate_need_target

        need_id = uuid4()
        need = MagicMock(spec=CommunityNeed)
        need.status = NeedStatus.OPEN

        db = AsyncMock()
        db.get.return_value = need

        # Should not raise
        await _validate_need_target(db, need_id)
        db.get.assert_awaited_once_with(CommunityNeed, need_id)

    @pytest.mark.asyncio
    async def test_raises_for_missing_need(self) -> None:
        from src.services.donation_target_service import (
            InvalidTargetError,
            _validate_need_target,
        )

        db = AsyncMock()
        db.get.return_value = None

        with pytest.raises(InvalidTargetError, match="not found"):
            await _validate_need_target(db, uuid4())

    @pytest.mark.asyncio
    async def test_raises_for_fulfilled_need(self) -> None:
        from src.services.donation_target_service import (
            TargetNotActiveError,
            _validate_need_target,
        )

        need = MagicMock(spec=CommunityNeed)
        need.status = NeedStatus.FULFILLED

        db = AsyncMock()
        db.get.return_value = need

        with pytest.raises(TargetNotActiveError, match="not open"):
            await _validate_need_target(db, uuid4())

    @pytest.mark.asyncio
    async def test_raises_for_cancelled_need(self) -> None:
        from src.services.donation_target_service import (
            TargetNotActiveError,
            _validate_need_target,
        )

        need = MagicMock(spec=CommunityNeed)
        need.status = NeedStatus.CANCELLED

        db = AsyncMock()
        db.get.return_value = need

        with pytest.raises(TargetNotActiveError, match="not open"):
            await _validate_need_target(db, uuid4())


# --- Schema validation tests ---


class TestNeedSchemas:
    """Tests for request/response schema validation."""

    def test_create_request_valid(self) -> None:
        from src.api.community_needs import NeedCreateRequest

        req = NeedCreateRequest(
            title="Alimento urgente",
            description="Necesitamos comida",
            category=NeedCategory.FOOD,
            estimated_cost_cents=5000,
            currency="USD",
        )
        assert req.title == "Alimento urgente"
        assert req.estimated_cost_cents == 5000

    def test_create_request_rejects_zero_cost(self) -> None:
        from pydantic import ValidationError
        from src.api.community_needs import NeedCreateRequest

        with pytest.raises(ValidationError):
            NeedCreateRequest(
                title="Test",
                description="Test desc",
                estimated_cost_cents=0,
            )

    def test_create_request_rejects_empty_title(self) -> None:
        from pydantic import ValidationError
        from src.api.community_needs import NeedCreateRequest

        with pytest.raises(ValidationError):
            NeedCreateRequest(
                title="",
                description="Test desc",
                estimated_cost_cents=1000,
            )

    def test_update_request_partial(self) -> None:
        from src.api.community_needs import NeedUpdateRequest

        req = NeedUpdateRequest(title="New title")
        dumped = req.model_dump(exclude_unset=True)
        assert dumped == {"title": "New title"}

    def test_update_request_status_change(self) -> None:
        from src.api.community_needs import NeedUpdateRequest

        req = NeedUpdateRequest(status=NeedStatus.FULFILLED)
        assert req.status == NeedStatus.FULFILLED
