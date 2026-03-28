"""Tests for intelligent transport request matching API."""

import pytest
from fastapi import HTTPException
from src.api.request_matching import (
    DEFAULT_SEARCH_RADIUS_KM,
    MATCH_EXPIRY_HOURS,
    MATCH_STATUS_LABELS_ES,
    MAX_MATCHES_PER_REQUEST,
    MAX_SEARCH_RADIUS_KM,
    NOTIFICATION_BATCH_SIZE,
    SAMPLE_DRIVERS,
    SCORE_LABELS_ES,
    URGENCY_LABELS_ES,
    MatchCriteria,
    MatchScore,
    MatchStatus,
    NotificationRequest,
    UrgencyLevel,
    VehicleType,
    _calculate_score,
    _reset_store,
    _score_to_tier,
    accept_match,
    decline_match,
    find_matches,
    get_matching_stats,
    get_request_matches,
    notify_matches,
    router,
)


@pytest.fixture(autouse=True)
def _clean_store() -> None:
    """Reset store before each test."""
    _reset_store()


# ---------------------------------------------------------------------------
# Enum tests
# ---------------------------------------------------------------------------


class TestEnums:
    """Verify enum members and labels."""

    def test_match_status_members(self) -> None:
        assert set(MatchStatus) == {
            MatchStatus.PENDING,
            MatchStatus.NOTIFIED,
            MatchStatus.ACCEPTED,
            MatchStatus.DECLINED,
            MatchStatus.EXPIRED,
            MatchStatus.CANCELLED,
        }

    def test_match_score_members(self) -> None:
        assert set(MatchScore) == {
            MatchScore.EXCELLENT,
            MatchScore.GOOD,
            MatchScore.FAIR,
            MatchScore.POOR,
        }

    def test_vehicle_type_members(self) -> None:
        assert set(VehicleType) == {
            VehicleType.CAR,
            VehicleType.SUV,
            VehicleType.VAN,
            VehicleType.TRUCK,
            VehicleType.MOTORCYCLE,
        }

    def test_urgency_level_members(self) -> None:
        assert set(UrgencyLevel) == {
            UrgencyLevel.EMERGENCY,
            UrgencyLevel.HIGH,
            UrgencyLevel.NORMAL,
            UrgencyLevel.LOW,
        }

    def test_status_labels_cover_all(self) -> None:
        for s in MatchStatus:
            assert s.value in MATCH_STATUS_LABELS_ES

    def test_score_labels_cover_all(self) -> None:
        for s in MatchScore:
            assert s.value in SCORE_LABELS_ES

    def test_urgency_labels_cover_all(self) -> None:
        for u in UrgencyLevel:
            assert u.value in URGENCY_LABELS_ES


# ---------------------------------------------------------------------------
# Constants tests
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify constant values."""

    def test_max_matches(self) -> None:
        assert MAX_MATCHES_PER_REQUEST == 10

    def test_default_radius(self) -> None:
        assert DEFAULT_SEARCH_RADIUS_KM == 25

    def test_max_radius(self) -> None:
        assert MAX_SEARCH_RADIUS_KM == 100

    def test_expiry_hours(self) -> None:
        assert MATCH_EXPIRY_HOURS == 24

    def test_notification_batch_size(self) -> None:
        assert NOTIFICATION_BATCH_SIZE == 5

    def test_sample_drivers_exist(self) -> None:
        assert len(SAMPLE_DRIVERS) == 5


# ---------------------------------------------------------------------------
# Router config tests
# ---------------------------------------------------------------------------


class TestRouterConfig:
    """Verify router setup."""

    def test_router_prefix(self) -> None:
        assert router.prefix == "/api/transport/matching"

    def test_router_tags(self) -> None:
        assert "request-matching" in router.tags


# ---------------------------------------------------------------------------
# Helper tests
# ---------------------------------------------------------------------------


class TestCalculateScore:
    """Test _calculate_score helper."""

    def test_returns_tuple(self) -> None:
        criteria = MatchCriteria(
            request_id="req-1",
            pickup_zone="Asuncion Centro",
            dropoff_zone="San Lorenzo",
        )
        result = _calculate_score(SAMPLE_DRIVERS[0], criteria)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_score_is_positive(self) -> None:
        criteria = MatchCriteria(
            request_id="req-1",
            pickup_zone="Asuncion Centro",
            dropoff_zone="San Lorenzo",
        )
        score, _ = _calculate_score(SAMPLE_DRIVERS[0], criteria)
        assert score > 0

    def test_breakdown_has_keys(self) -> None:
        criteria = MatchCriteria(
            request_id="req-1",
            pickup_zone="Asuncion Centro",
            dropoff_zone="San Lorenzo",
        )
        _, breakdown = _calculate_score(SAMPLE_DRIVERS[0], criteria)
        assert "vehicle" in breakdown
        assert "proximity" in breakdown
        assert "rating" in breakdown
        assert "urgency" in breakdown

    def test_exact_vehicle_match_scores_higher(self) -> None:
        criteria_car = MatchCriteria(
            request_id="req-1",
            pickup_zone="Luque",
            dropoff_zone="San Lorenzo",
            vehicle_needed=VehicleType.CAR,
        )
        # drv-003 has CAR
        score_match, _ = _calculate_score(SAMPLE_DRIVERS[2], criteria_car)
        criteria_truck = MatchCriteria(
            request_id="req-1",
            pickup_zone="Luque",
            dropoff_zone="San Lorenzo",
            vehicle_needed=VehicleType.TRUCK,
        )
        score_mismatch, _ = _calculate_score(SAMPLE_DRIVERS[2], criteria_truck)
        assert score_match >= score_mismatch

    def test_zone_match_scores_higher(self) -> None:
        criteria_same = MatchCriteria(
            request_id="req-1",
            pickup_zone="Asuncion Centro",
            dropoff_zone="San Lorenzo",
        )
        criteria_diff = MatchCriteria(
            request_id="req-1",
            pickup_zone="Far Away Zone",
            dropoff_zone="San Lorenzo",
        )
        # drv-001 is in Asuncion Centro
        score_same, _ = _calculate_score(SAMPLE_DRIVERS[0], criteria_same)
        score_diff, _ = _calculate_score(SAMPLE_DRIVERS[0], criteria_diff)
        assert score_same > score_diff


class TestScoreToTier:
    """Test _score_to_tier helper."""

    def test_excellent(self) -> None:
        assert _score_to_tier(90.0) == MatchScore.EXCELLENT

    def test_good(self) -> None:
        assert _score_to_tier(75.0) == MatchScore.GOOD

    def test_fair(self) -> None:
        assert _score_to_tier(60.0) == MatchScore.FAIR

    def test_poor(self) -> None:
        assert _score_to_tier(40.0) == MatchScore.POOR

    def test_boundary_excellent(self) -> None:
        assert _score_to_tier(85.0) == MatchScore.EXCELLENT

    def test_boundary_good(self) -> None:
        assert _score_to_tier(70.0) == MatchScore.GOOD

    def test_boundary_fair(self) -> None:
        assert _score_to_tier(55.0) == MatchScore.FAIR


# ---------------------------------------------------------------------------
# Endpoint tests
# ---------------------------------------------------------------------------


class TestFindMatches:
    """Test POST /find endpoint."""

    @pytest.mark.asyncio
    async def test_finds_matches(self) -> None:
        criteria = MatchCriteria(
            request_id="req-test-1",
            pickup_zone="Asuncion Centro",
            dropoff_zone="San Lorenzo",
        )
        result = await find_matches(criteria)
        assert result.matches_found > 0
        assert result.request_id == "req-test-1"

    @pytest.mark.asyncio
    async def test_matches_sorted_by_score(self) -> None:
        criteria = MatchCriteria(
            request_id="req-test-2",
            pickup_zone="Asuncion Centro",
            dropoff_zone="San Lorenzo",
        )
        result = await find_matches(criteria)
        scores = [m.score for m in result.matches]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_matches_have_valid_status(self) -> None:
        criteria = MatchCriteria(
            request_id="req-test-3",
            pickup_zone="Asuncion Centro",
            dropoff_zone="San Lorenzo",
        )
        result = await find_matches(criteria)
        for m in result.matches:
            assert m.status == MatchStatus.PENDING

    @pytest.mark.asyncio
    async def test_matches_have_score_breakdown(self) -> None:
        criteria = MatchCriteria(
            request_id="req-test-4",
            pickup_zone="Asuncion Centro",
            dropoff_zone="San Lorenzo",
        )
        result = await find_matches(criteria)
        for m in result.matches:
            assert len(m.score_breakdown) > 0

    @pytest.mark.asyncio
    async def test_respects_max_radius(self) -> None:
        criteria = MatchCriteria(
            request_id="req-test-5",
            pickup_zone="Asuncion Centro",
            dropoff_zone="San Lorenzo",
            search_radius_km=MAX_SEARCH_RADIUS_KM + 1,
        )
        with pytest.raises(HTTPException):
            await find_matches(criteria)


class TestGetRequestMatches:
    """Test GET /{request_id} endpoint."""

    @pytest.mark.asyncio
    async def test_returns_matches_after_find(self) -> None:
        criteria = MatchCriteria(
            request_id="req-get-1",
            pickup_zone="Asuncion Centro",
            dropoff_zone="San Lorenzo",
        )
        await find_matches(criteria)
        result = await get_request_matches("req-get-1")
        assert result.matches_found > 0

    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        with pytest.raises(HTTPException):
            await get_request_matches("nonexistent-request")


class TestAcceptMatch:
    """Test POST /{match_id}/accept endpoint."""

    @pytest.mark.asyncio
    async def test_accept_pending_match(self) -> None:
        criteria = MatchCriteria(
            request_id="req-accept-1",
            pickup_zone="Asuncion Centro",
            dropoff_zone="San Lorenzo",
        )
        result = await find_matches(criteria)
        match_id = result.matches[0].match_id
        response = await accept_match(match_id)
        assert response.status == MatchStatus.ACCEPTED
        assert response.responded_at is not None

    @pytest.mark.asyncio
    async def test_accept_nonexistent_raises(self) -> None:
        with pytest.raises(HTTPException):
            await accept_match("nonexistent-match")

    @pytest.mark.asyncio
    async def test_accept_already_accepted_raises(self) -> None:
        criteria = MatchCriteria(
            request_id="req-accept-2",
            pickup_zone="Asuncion Centro",
            dropoff_zone="San Lorenzo",
        )
        result = await find_matches(criteria)
        match_id = result.matches[0].match_id
        await accept_match(match_id)
        with pytest.raises(HTTPException):
            await accept_match(match_id)


class TestDeclineMatch:
    """Test POST /{match_id}/decline endpoint."""

    @pytest.mark.asyncio
    async def test_decline_pending_match(self) -> None:
        criteria = MatchCriteria(
            request_id="req-decline-1",
            pickup_zone="Asuncion Centro",
            dropoff_zone="San Lorenzo",
        )
        result = await find_matches(criteria)
        match_id = result.matches[0].match_id
        response = await decline_match(match_id)
        assert response.status == MatchStatus.DECLINED

    @pytest.mark.asyncio
    async def test_decline_nonexistent_raises(self) -> None:
        with pytest.raises(HTTPException):
            await decline_match("nonexistent-match")


class TestNotifyMatches:
    """Test POST /notify endpoint."""

    @pytest.mark.asyncio
    async def test_notify_all_matches(self) -> None:
        criteria = MatchCriteria(
            request_id="req-notify-1",
            pickup_zone="Asuncion Centro",
            dropoff_zone="San Lorenzo",
        )
        await find_matches(criteria)
        request = NotificationRequest(request_id="req-notify-1")
        result = await notify_matches(request)
        assert result.notifications_sent > 0
        assert result.notifications_failed == 0

    @pytest.mark.asyncio
    async def test_notify_specific_matches(self) -> None:
        criteria = MatchCriteria(
            request_id="req-notify-2",
            pickup_zone="Asuncion Centro",
            dropoff_zone="San Lorenzo",
        )
        find_result = await find_matches(criteria)
        first_id = find_result.matches[0].match_id
        request = NotificationRequest(request_id="req-notify-2", match_ids=[first_id])
        result = await notify_matches(request)
        assert result.notifications_sent == 1

    @pytest.mark.asyncio
    async def test_notify_nonexistent_match_fails(self) -> None:
        request = NotificationRequest(request_id="req-notify-3", match_ids=["nonexistent"])
        result = await notify_matches(request)
        assert result.notifications_failed == 1
        assert result.notifications_sent == 0


class TestMatchingStats:
    """Test GET /stats endpoint."""

    @pytest.mark.asyncio
    async def test_empty_stats(self) -> None:
        result = await get_matching_stats()
        assert result.total_matches_created == 0
        assert result.acceptance_rate_pct == 0.0

    @pytest.mark.asyncio
    async def test_stats_after_matches(self) -> None:
        criteria = MatchCriteria(
            request_id="req-stats-1",
            pickup_zone="Asuncion Centro",
            dropoff_zone="San Lorenzo",
        )
        find_result = await find_matches(criteria)
        await accept_match(find_result.matches[0].match_id)

        result = await get_matching_stats()
        assert result.total_matches_created == len(find_result.matches)
        assert result.matches_accepted == 1

    @pytest.mark.asyncio
    async def test_stats_has_zones(self) -> None:
        result = await get_matching_stats()
        assert isinstance(result.top_zones, list)
        assert len(result.top_zones) > 0

    @pytest.mark.asyncio
    async def test_stats_has_busiest_days(self) -> None:
        result = await get_matching_stats()
        assert isinstance(result.busiest_days, list)
        assert len(result.busiest_days) > 0


# ---------------------------------------------------------------------------
# Frontend file assertions
# ---------------------------------------------------------------------------


class TestFrontendFile:
    """Verify frontend page exists."""

    def test_page_file_exists(self) -> None:
        from pathlib import Path

        page = Path("frontend/src/app/admin/transporte/matching/page.tsx")
        assert page.exists(), "Frontend page must exist"
        content = page.read_text()
        assert "RequestMatchingPage" in content
        assert "Matching de transporte" in content
