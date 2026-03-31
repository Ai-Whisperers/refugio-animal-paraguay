"""Unit tests for community engagement analytics API (RAP-637)."""

from pathlib import Path

import pytest
from src.api.community_engagement_analytics import (
    CHANNEL_LABELS_ES,
    DEFAULT_PERIOD_DAYS,
    GROWTH_LABELS_ES,
    ChannelEngagement,
    CommunityGrowth,
    EngagementBreakdown,
    EngagementChannel,
    EngagementKPI,
    EngagementOverview,
    EventMetrics,
    GrowthMetric,
    GrowthTrend,
    SocialMetrics,
    VolunteerMetrics,
    get_community_growth,
    get_engagement_breakdown,
    get_engagement_overview,
    get_event_metrics,
    get_social_metrics,
    get_volunteer_metrics,
    router,
)


class TestEnums:
    def test_engagement_channel_values(self):
        assert len(EngagementChannel) == 6
        assert EngagementChannel.VOLUNTEERING == "volunteering"
        assert EngagementChannel.SOCIAL_MEDIA == "social_media"

    def test_growth_metric_values(self):
        assert len(GrowthMetric) == 5
        assert GrowthMetric.NEW_VOLUNTEERS == "new_volunteers"

    def test_channel_labels_spanish(self):
        assert len(CHANNEL_LABELS_ES) == len(EngagementChannel)
        for ch in EngagementChannel:
            assert ch in CHANNEL_LABELS_ES

    def test_growth_labels_spanish(self):
        assert len(GROWTH_LABELS_ES) == len(GrowthMetric)
        for gm in GrowthMetric:
            assert gm in GROWTH_LABELS_ES


class TestSchemas:
    def test_engagement_kpi(self):
        kpi = EngagementKPI(label="Test", value=42, change_pct=5.0, trend="up")
        assert kpi.label == "Test"
        assert kpi.value == 42

    def test_growth_trend(self):
        gt = GrowthTrend(month="2026-01", metric=GrowthMetric.NEW_DONORS, value=10, cumulative=100)
        assert gt.metric == GrowthMetric.NEW_DONORS
        assert gt.cumulative == 100

    def test_channel_engagement(self):
        ce = ChannelEngagement(
            channel=EngagementChannel.EVENTS,
            label="Eventos",
            score=71.0,
            active_users=156,
            interactions=580,
            trend="up",
        )
        assert ce.score == 71.0


class TestRouterConfig:
    def test_router_prefix(self):
        assert router.prefix == "/api/admin/analytics/community"

    def test_router_tags(self):
        assert "community-analytics" in router.tags


class TestGetOverview:
    @pytest.mark.asyncio
    async def test_overview_default_period(self):
        result = await get_engagement_overview(period_days=DEFAULT_PERIOD_DAYS)
        assert isinstance(result, EngagementOverview)
        assert result.period_days == 30
        assert result.total_active_members > 0
        assert result.engagement_score > 0
        assert len(result.kpis) > 0

    @pytest.mark.asyncio
    async def test_overview_custom_period(self):
        result = await get_engagement_overview(period_days=90)
        assert result.period_days == 90

    @pytest.mark.asyncio
    async def test_overview_kpis_have_required_fields(self):
        result = await get_engagement_overview(period_days=30)
        for kpi in result.kpis:
            assert kpi.label
            assert kpi.trend in ("up", "down", "stable")

    @pytest.mark.asyncio
    async def test_overview_has_timestamp(self):
        result = await get_engagement_overview(period_days=30)
        assert result.generated_at is not None


class TestGetVolunteerMetrics:
    @pytest.mark.asyncio
    async def test_volunteer_metrics(self):
        result = await get_volunteer_metrics()
        assert isinstance(result, VolunteerMetrics)
        assert result.total_volunteers > 0
        assert result.active_this_period > 0
        assert result.total_hours > 0

    @pytest.mark.asyncio
    async def test_volunteer_top_activities(self):
        result = await get_volunteer_metrics()
        assert len(result.top_activities) > 0
        for act in result.top_activities:
            assert "activity" in act
            assert "hours" in act

    @pytest.mark.asyncio
    async def test_volunteer_monthly_hours(self):
        result = await get_volunteer_metrics()
        assert len(result.monthly_hours) > 0


class TestGetEventMetrics:
    @pytest.mark.asyncio
    async def test_event_metrics(self):
        result = await get_event_metrics()
        assert isinstance(result, EventMetrics)
        assert result.total_events > 0
        assert result.total_attendees > 0

    @pytest.mark.asyncio
    async def test_event_types(self):
        result = await get_event_metrics()
        assert len(result.events_by_type) > 0

    @pytest.mark.asyncio
    async def test_monthly_events(self):
        result = await get_event_metrics()
        assert len(result.monthly_events) > 0


class TestGetSocialMetrics:
    @pytest.mark.asyncio
    async def test_social_metrics(self):
        result = await get_social_metrics()
        assert isinstance(result, SocialMetrics)
        assert result.total_followers > 0
        assert result.engagement_rate > 0

    @pytest.mark.asyncio
    async def test_platforms(self):
        result = await get_social_metrics()
        assert len(result.platforms) > 0
        for p in result.platforms:
            assert "platform" in p
            assert "followers" in p

    @pytest.mark.asyncio
    async def test_monthly_reach(self):
        result = await get_social_metrics()
        assert len(result.monthly_reach) > 0


class TestGetCommunityGrowth:
    @pytest.mark.asyncio
    async def test_growth_data(self):
        result = await get_community_growth(period_days=30)
        assert isinstance(result, CommunityGrowth)
        assert result.period_days == 30
        assert len(result.trends) > 0

    @pytest.mark.asyncio
    async def test_growth_summary(self):
        result = await get_community_growth(period_days=30)
        assert "total_new_volunteers" in result.summary

    @pytest.mark.asyncio
    async def test_growth_trends_cumulative(self):
        result = await get_community_growth(period_days=30)
        for trend in result.trends:
            assert trend.cumulative >= trend.value


class TestGetEngagementBreakdown:
    @pytest.mark.asyncio
    async def test_breakdown(self):
        result = await get_engagement_breakdown()
        assert isinstance(result, EngagementBreakdown)
        assert result.overall_score > 0
        assert len(result.channels) > 0

    @pytest.mark.asyncio
    async def test_channels_have_scores(self):
        result = await get_engagement_breakdown()
        for ch in result.channels:
            assert 0 <= ch.score <= 100
            assert ch.trend in ("up", "down", "stable")

    @pytest.mark.asyncio
    async def test_channels_have_labels(self):
        result = await get_engagement_breakdown()
        for ch in result.channels:
            assert ch.label


class TestFrontendPage:
    def test_file_exists(self):
        assert Path("frontend/src/app/admin/analytics/comunidad/page.tsx").exists()

    def test_contains_use_client(self):
        content = Path("frontend/src/app/admin/analytics/comunidad/page.tsx").read_text()
        assert '"use client"' in content

    def test_contains_sections(self):
        content = Path("frontend/src/app/admin/analytics/comunidad/page.tsx").read_text()
        assert "VolunteerSection" in content
        assert "EventSection" in content

    def test_responsive(self):
        content = Path("frontend/src/app/admin/analytics/comunidad/page.tsx").read_text()
        assert "md:" in content or "lg:" in content
