"""Unit tests for community feed service."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services.community_feed_service import (
    FEED_PAGE_SIZE,
    FeedItemType,
    _fetch_animals,
    _fetch_campaigns,
    _fetch_needs,
    _fetch_success_stories,
    _haversine_km,
    _within_radius,
    get_community_feed,
)

# ---------------------------------------------------------------------------
# Haversine
# ---------------------------------------------------------------------------


class TestHaversine:
    """Tests for great-circle distance calculation."""

    def test_same_point_returns_zero(self) -> None:
        assert _haversine_km(0, 0, 0, 0) == pytest.approx(0.0)

    def test_known_distance_asuncion_to_bsas(self) -> None:
        # Asuncion (-25.286, -57.647) to Buenos Aires (-34.603, -58.381)
        dist = _haversine_km(-25.286, -57.647, -34.603, -58.381)
        assert 1000 < dist < 1400  # ~1200 km

    def test_returns_float(self) -> None:
        result = _haversine_km(0.0, 0.0, 1.0, 0.0)
        assert isinstance(result, float)


# ---------------------------------------------------------------------------
# _within_radius
# ---------------------------------------------------------------------------


class TestWithinRadius:
    """Tests for location radius filter."""

    def test_no_filter_always_passes(self) -> None:
        assert _within_radius(None, None, None, 100) is True

    def test_no_coords_passes_when_filter_active(self) -> None:
        # Items without location coords are always included
        assert _within_radius(None, -25.286, -57.647, 100) is True

    def test_coords_inside_radius(self) -> None:
        # Same city — distance is ~0
        coords = {"lat": -25.286, "lng": -57.647}
        assert _within_radius(coords, -25.286, -57.647, 100) is True

    def test_coords_outside_radius(self) -> None:
        # Buenos Aires vs Asunción: ~1200 km
        coords = {"lat": -34.603, "lng": -58.381}
        assert _within_radius(coords, -25.286, -57.647, 100) is False

    def test_alternative_coord_key_names(self) -> None:
        coords = {"latitude": -25.286, "longitude": -57.647}
        assert _within_radius(coords, -25.286, -57.647, 50) is True

    def test_empty_coords_dict_passes(self) -> None:
        # Missing lat/lng keys → no filtering
        assert _within_radius({}, -25.286, -57.647, 100) is True


# ---------------------------------------------------------------------------
# _fetch_animals
# ---------------------------------------------------------------------------


def _make_mock_animal() -> MagicMock:
    animal = MagicMock()
    animal.id = uuid4()
    animal.name = "Rex"
    animal.species = "dog"
    animal.breed = "Mestizo"
    animal.description = "Friendly dog looking for a home."
    animal.primary_photo_url = None
    animal.created_at = datetime(2026, 1, 15, tzinfo=UTC)
    return animal


class TestFetchAnimals:
    """Tests for animal feed source."""

    @pytest.mark.asyncio
    async def test_returns_animal_items(self) -> None:
        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = [_make_mock_animal()]
        db.execute.return_value = result

        items = await _fetch_animals(db, limit=10)

        assert len(items) == 1
        assert items[0]["event_type"] == FeedItemType.ANIMAL

    @pytest.mark.asyncio
    async def test_item_has_required_keys(self) -> None:
        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = [_make_mock_animal()]
        db.execute.return_value = result

        items = await _fetch_animals(db, limit=10)
        item = items[0]

        assert "id" in item
        assert "title" in item
        assert "preview" in item
        assert "timestamp" in item
        assert "detail_url" in item
        assert "badge" in item

    @pytest.mark.asyncio
    async def test_title_includes_animal_name(self) -> None:
        db = AsyncMock()
        result = MagicMock()
        animal = _make_mock_animal()
        animal.name = "Luna"
        result.scalars.return_value.all.return_value = [animal]
        db.execute.return_value = result

        items = await _fetch_animals(db, limit=10)

        assert "Luna" in items[0]["title"]

    @pytest.mark.asyncio
    async def test_preview_truncates_long_description(self) -> None:
        db = AsyncMock()
        result = MagicMock()
        animal = _make_mock_animal()
        animal.description = "A" * 200
        result.scalars.return_value.all.return_value = [animal]
        db.execute.return_value = result

        items = await _fetch_animals(db, limit=10)
        preview = items[0]["preview"]

        assert len(preview) <= 155  # 150 chars + "…"
        assert preview.endswith("…")

    @pytest.mark.asyncio
    async def test_empty_db_returns_empty_list(self) -> None:
        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        db.execute.return_value = result

        items = await _fetch_animals(db, limit=10)

        assert items == []


# ---------------------------------------------------------------------------
# _fetch_campaigns
# ---------------------------------------------------------------------------


def _make_mock_campaign() -> MagicMock:
    campaign = MagicMock()
    campaign.id = uuid4()
    campaign.title = "Help feed 50 dogs"
    campaign.description = "Monthly food fund for shelter dogs."
    campaign.image_url = None
    campaign.target_amount_cents = 50000
    campaign.fund_category = "food"
    campaign.created_at = datetime(2026, 2, 10, tzinfo=UTC)
    return campaign


class TestFetchCampaigns:
    """Tests for campaign feed source."""

    @pytest.mark.asyncio
    async def test_returns_campaign_items(self) -> None:
        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = [_make_mock_campaign()]
        db.execute.return_value = result

        items = await _fetch_campaigns(db, limit=10)

        assert len(items) == 1
        assert items[0]["event_type"] == FeedItemType.CAMPAIGN

    @pytest.mark.asyncio
    async def test_target_eur_converts_from_cents(self) -> None:
        db = AsyncMock()
        result = MagicMock()
        campaign = _make_mock_campaign()
        campaign.target_amount_cents = 10000  # €100
        result.scalars.return_value.all.return_value = [campaign]
        db.execute.return_value = result

        items = await _fetch_campaigns(db, limit=10)

        assert items[0]["target_eur"] == pytest.approx(100.0)


# ---------------------------------------------------------------------------
# _fetch_needs
# ---------------------------------------------------------------------------


def _make_mock_need() -> MagicMock:
    need = MagicMock()
    need.id = uuid4()
    need.title = "Urgent: food for 10 cats"
    need.description = "We need food donations urgently."
    need.category = "food"
    need.estimated_cost_cents = 3000
    need.currency = "USD"
    need.image_url = None
    need.created_at = datetime(2026, 3, 1, tzinfo=UTC)
    return need


class TestFetchNeeds:
    """Tests for community needs feed source."""

    @pytest.mark.asyncio
    async def test_returns_need_items(self) -> None:
        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = [_make_mock_need()]
        db.execute.return_value = result

        items = await _fetch_needs(db, limit=10)

        assert len(items) == 1
        assert items[0]["event_type"] == FeedItemType.NEED

    @pytest.mark.asyncio
    async def test_need_item_detail_url(self) -> None:
        db = AsyncMock()
        result = MagicMock()
        need = _make_mock_need()
        result.scalars.return_value.all.return_value = [need]
        db.execute.return_value = result

        items = await _fetch_needs(db, limit=10)

        assert items[0]["detail_url"] == f"/needs/{need.id}"


# ---------------------------------------------------------------------------
# _fetch_success_stories
# ---------------------------------------------------------------------------


def _make_mock_story() -> MagicMock:
    story = MagicMock()
    story.id = uuid4()
    story.title = "Max found his forever home"
    story.story_text = "Max was adopted by the Garcia family."
    story.quote = "He's perfect."
    story.photo_url = "https://example.com/photo.jpg"
    story.adopter_name = "Garcia Family"
    story.is_featured = False
    story.published_at = datetime(2026, 3, 10, tzinfo=UTC)
    return story


class TestFetchSuccessStories:
    """Tests for success story feed source."""

    @pytest.mark.asyncio
    async def test_returns_success_items(self) -> None:
        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = [_make_mock_story()]
        db.execute.return_value = result

        items = await _fetch_success_stories(db, limit=10)

        assert len(items) == 1
        assert items[0]["event_type"] == FeedItemType.SUCCESS

    @pytest.mark.asyncio
    async def test_preview_prefers_quote(self) -> None:
        db = AsyncMock()
        result = MagicMock()
        story = _make_mock_story()
        story.quote = "Best adoption ever!"
        story.story_text = "Long story text"
        result.scalars.return_value.all.return_value = [story]
        db.execute.return_value = result

        items = await _fetch_success_stories(db, limit=10)

        assert "Best adoption ever!" in items[0]["preview"]


# ---------------------------------------------------------------------------
# get_community_feed
# ---------------------------------------------------------------------------


class TestGetCommunityFeed:
    """Integration-level tests for the main feed aggregation."""

    @pytest.mark.asyncio
    async def test_merges_all_sources(self) -> None:
        db = AsyncMock()
        animal = _make_mock_animal()
        campaign = _make_mock_campaign()
        need = _make_mock_need()
        story = _make_mock_story()

        # Each call to db.execute returns a different result
        results = []
        for objs in [[animal], [campaign], [need], [story]]:
            r = MagicMock()
            r.scalars.return_value.all.return_value = objs
            results.append(r)
        db.execute.side_effect = results

        feed = await get_community_feed(db)

        assert len(feed["items"]) == 4

    @pytest.mark.asyncio
    async def test_default_page_size(self) -> None:
        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        db.execute.return_value = result

        feed = await get_community_feed(db)

        assert feed["page_size"] == FEED_PAGE_SIZE

    @pytest.mark.asyncio
    async def test_sorted_newest_first(self) -> None:
        db = AsyncMock()

        older_animal = _make_mock_animal()
        older_animal.created_at = datetime(2026, 1, 1, tzinfo=UTC)
        newer_animal = _make_mock_animal()
        newer_animal.created_at = datetime(2026, 3, 1, tzinfo=UTC)

        results = []
        for objs in [[older_animal, newer_animal], [], [], []]:
            r = MagicMock()
            r.scalars.return_value.all.return_value = objs
            results.append(r)
        db.execute.side_effect = results

        feed = await get_community_feed(db)

        timestamps = [item["timestamp"] for item in feed["items"]]
        assert timestamps == sorted(timestamps, reverse=True)

    @pytest.mark.asyncio
    async def test_type_filter_excludes_others(self) -> None:
        db = AsyncMock()

        animal = _make_mock_animal()
        result = MagicMock()
        result.scalars.return_value.all.return_value = [animal]
        db.execute.return_value = result

        feed = await get_community_feed(db, item_types=[FeedItemType.ANIMAL])

        assert all(item["event_type"] == FeedItemType.ANIMAL for item in feed["items"])

    @pytest.mark.asyncio
    async def test_pagination_has_next(self) -> None:
        db = AsyncMock()
        # Return 25 animals (more than default page_size=20)
        animals = [_make_mock_animal() for _ in range(25)]
        for i, a in enumerate(animals):
            a.created_at = datetime(2026, 1, i + 1, tzinfo=UTC)

        results = []
        for objs in [animals, [], [], []]:
            r = MagicMock()
            r.scalars.return_value.all.return_value = objs
            results.append(r)
        db.execute.side_effect = results

        feed = await get_community_feed(db, page=1, page_size=20)

        assert feed["has_next"] is True
        assert len(feed["items"]) == 20

    @pytest.mark.asyncio
    async def test_page_size_capped_at_50(self) -> None:
        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        db.execute.return_value = result

        feed = await get_community_feed(db, page_size=999)

        assert feed["page_size"] == 50

    @pytest.mark.asyncio
    async def test_location_filter_excludes_distant_items(self) -> None:
        db = AsyncMock()

        # Two campaigns — one with no coords (passes), one far away (fails)
        near_campaign = _make_mock_campaign()
        near_campaign.image_url = None

        far_campaign = _make_mock_campaign()
        far_campaign.title = "Far away campaign"
        far_campaign.image_url = None

        results = []
        for objs in [[], [near_campaign, far_campaign], [], []]:
            r = MagicMock()
            r.scalars.return_value.all.return_value = objs
            results.append(r)
        db.execute.side_effect = results

        # Both campaigns have no location_coords → both pass through
        feed = await get_community_feed(db, lat=-25.286, lng=-57.647, radius_km=100)

        assert len(feed["items"]) == 2  # no coords → both included
