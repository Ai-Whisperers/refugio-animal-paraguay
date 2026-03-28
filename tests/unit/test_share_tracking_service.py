"""Unit tests for share tracking service."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services.share_tracking_service import (
    InvalidEntityTypeError,
    InvalidPlatformError,
    ShareTrackingError,
    get_share_analytics,
    get_top_shared,
    track_share,
    validate_entity_type,
    validate_platform,
)

# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------


class TestValidateEntityType:
    """Tests for entity type validation."""

    def test_valid_entity_types(self) -> None:
        for et in ("animal", "campaign", "story", "blog_post"):
            validate_entity_type(et)

    def test_invalid_entity_type_raises(self) -> None:
        with pytest.raises(InvalidEntityTypeError):
            validate_entity_type("video")

    def test_empty_string_raises(self) -> None:
        with pytest.raises(InvalidEntityTypeError):
            validate_entity_type("")


class TestValidatePlatform:
    """Tests for platform validation."""

    def test_valid_platforms(self) -> None:
        for p in ("whatsapp", "facebook", "twitter", "copy_link", "native_share"):
            validate_platform(p)

    def test_invalid_platform_raises(self) -> None:
        with pytest.raises(InvalidPlatformError):
            validate_platform("instagram")

    def test_empty_string_raises(self) -> None:
        with pytest.raises(InvalidPlatformError):
            validate_platform("")


# ---------------------------------------------------------------------------
# track_share
# ---------------------------------------------------------------------------


class TestTrackShare:
    """Tests for share event recording."""

    @pytest.fixture()
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.mark.asyncio()
    async def test_creates_share_event(self, mock_db: AsyncMock) -> None:
        entity_id = uuid4()
        event = await track_share(
            entity_type="animal",
            entity_id=entity_id,
            platform="whatsapp",
            db=mock_db,
        )
        assert event.entity_type == "animal"
        assert event.entity_id == entity_id
        assert event.platform == "whatsapp"
        assert event.sharer_user_id is None
        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_records_user_and_ip(self, mock_db: AsyncMock) -> None:
        user_id = uuid4()
        event = await track_share(
            entity_type="campaign",
            entity_id=uuid4(),
            platform="facebook",
            sharer_user_id=user_id,
            ip_address="192.168.1.1",
            db=mock_db,
        )
        assert event.sharer_user_id == user_id
        assert event.ip_address == "192.168.1.1"

    @pytest.mark.asyncio()
    async def test_rejects_invalid_entity_type(self, mock_db: AsyncMock) -> None:
        with pytest.raises(InvalidEntityTypeError):
            await track_share(
                entity_type="video",
                entity_id=uuid4(),
                platform="whatsapp",
                db=mock_db,
            )

    @pytest.mark.asyncio()
    async def test_rejects_invalid_platform(self, mock_db: AsyncMock) -> None:
        with pytest.raises(InvalidPlatformError):
            await track_share(
                entity_type="animal",
                entity_id=uuid4(),
                platform="instagram",
                db=mock_db,
            )

    @pytest.mark.asyncio()
    async def test_all_entity_types_accepted(self, mock_db: AsyncMock) -> None:
        for et in ("animal", "campaign", "story", "blog_post"):
            event = await track_share(
                entity_type=et,
                entity_id=uuid4(),
                platform="copy_link",
                db=mock_db,
            )
            assert event.entity_type == et

    @pytest.mark.asyncio()
    async def test_all_platforms_accepted(self, mock_db: AsyncMock) -> None:
        for p in ("whatsapp", "facebook", "twitter", "copy_link", "native_share"):
            event = await track_share(
                entity_type="animal",
                entity_id=uuid4(),
                platform=p,
                db=mock_db,
            )
            assert event.platform == p


# ---------------------------------------------------------------------------
# get_share_analytics
# ---------------------------------------------------------------------------


class TestGetShareAnalytics:
    """Tests for share analytics aggregation."""

    @pytest.mark.asyncio()
    async def test_returns_analytics_structure(self) -> None:
        db = AsyncMock()

        # Total shares
        total_result = MagicMock()
        total_result.scalar_one.return_value = 42

        # Platform breakdown
        platform_result = MagicMock()
        platform_result.all.return_value = [("whatsapp", 20), ("facebook", 15), ("twitter", 7)]

        # Entity type breakdown
        entity_result = MagicMock()
        entity_result.all.return_value = [("animal", 30), ("campaign", 12)]

        # Daily shares
        daily_result = MagicMock()
        daily_result.all.return_value = []

        db.execute.side_effect = [total_result, platform_result, entity_result, daily_result]

        analytics = await get_share_analytics(db)
        assert analytics["total_shares"] == 42
        assert analytics["shares_by_platform"]["whatsapp"] == 20
        assert analytics["shares_by_platform"]["facebook"] == 15
        assert analytics["shares_by_entity_type"]["animal"] == 30
        assert analytics["period_days"] == 30

    @pytest.mark.asyncio()
    async def test_filters_by_entity_type(self) -> None:
        db = AsyncMock()
        total_result = MagicMock()
        total_result.scalar_one.return_value = 10
        platform_result = MagicMock()
        platform_result.all.return_value = []
        entity_result = MagicMock()
        entity_result.all.return_value = [("animal", 10)]
        daily_result = MagicMock()
        daily_result.all.return_value = []
        db.execute.side_effect = [total_result, platform_result, entity_result, daily_result]

        analytics = await get_share_analytics(db, entity_type="animal")
        assert analytics["total_shares"] == 10

    @pytest.mark.asyncio()
    async def test_rejects_invalid_entity_type_filter(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidEntityTypeError):
            await get_share_analytics(db, entity_type="invalid")

    @pytest.mark.asyncio()
    async def test_custom_days_period(self) -> None:
        db = AsyncMock()
        total_result = MagicMock()
        total_result.scalar_one.return_value = 5
        platform_result = MagicMock()
        platform_result.all.return_value = []
        entity_result = MagicMock()
        entity_result.all.return_value = []
        daily_result = MagicMock()
        daily_result.all.return_value = []
        db.execute.side_effect = [total_result, platform_result, entity_result, daily_result]

        analytics = await get_share_analytics(db, days=7)
        assert analytics["period_days"] == 7


# ---------------------------------------------------------------------------
# get_top_shared
# ---------------------------------------------------------------------------


class TestGetTopShared:
    """Tests for top-shared content ranking."""

    @pytest.mark.asyncio()
    async def test_returns_ranked_entities(self) -> None:
        entity1 = uuid4()
        entity2 = uuid4()

        db = AsyncMock()
        # Main ranking query
        rank_result = MagicMock()
        rank_result.all.return_value = [(entity1, 15), (entity2, 8)]

        # Platform breakdowns (one per entity)
        platform1 = MagicMock()
        platform1.all.return_value = [("whatsapp", 10), ("facebook", 5)]
        platform2 = MagicMock()
        platform2.all.return_value = [("twitter", 8)]

        db.execute.side_effect = [rank_result, platform1, platform2]

        items = await get_top_shared(db, entity_type="animal")
        assert len(items) == 2
        assert items[0]["entity_id"] == str(entity1)
        assert items[0]["share_count"] == 15
        assert items[0]["platforms"]["whatsapp"] == 10
        assert items[1]["share_count"] == 8

    @pytest.mark.asyncio()
    async def test_returns_empty_for_no_shares(self) -> None:
        db = AsyncMock()
        rank_result = MagicMock()
        rank_result.all.return_value = []
        db.execute.return_value = rank_result

        items = await get_top_shared(db, entity_type="campaign")
        assert items == []

    @pytest.mark.asyncio()
    async def test_rejects_invalid_entity_type(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidEntityTypeError):
            await get_top_shared(db, entity_type="invalid")


# ---------------------------------------------------------------------------
# Error classes
# ---------------------------------------------------------------------------


class TestErrorClasses:
    """Tests for error hierarchy."""

    def test_base_error(self) -> None:
        err = ShareTrackingError("test", "details")
        assert err.message == "test"
        assert err.details == "details"

    def test_invalid_entity_type_error(self) -> None:
        err = InvalidEntityTypeError("video")
        assert err.message == "Invalid entity type"
        assert "animal" in err.details

    def test_invalid_platform_error(self) -> None:
        err = InvalidPlatformError("instagram")
        assert err.message == "Invalid platform"
        assert "whatsapp" in err.details
