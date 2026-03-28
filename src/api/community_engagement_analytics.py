"""Community engagement analytics API (RAP-637).

Provides analytics on community engagement metrics including volunteer
activity, adoption trends, event participation, social media reach,
and donor engagement patterns.

Endpoints:
    GET /api/admin/analytics/community/overview     -- engagement overview KPIs
    GET /api/admin/analytics/community/volunteers    -- volunteer activity metrics
    GET /api/admin/analytics/community/events        -- event participation analytics
    GET /api/admin/analytics/community/social        -- social media reach metrics
    GET /api/admin/analytics/community/growth        -- community growth trends
    GET /api/admin/analytics/community/engagement    -- engagement score breakdown
"""

import logging
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/analytics/community",
    tags=["community-analytics"],
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PERIOD_DAYS = 30
MAX_PERIOD_DAYS = 365


class EngagementChannel(StrEnum):
    """Community engagement channels."""

    VOLUNTEERING = "volunteering"
    DONATIONS = "donations"
    ADOPTIONS = "adoptions"
    EVENTS = "events"
    SOCIAL_MEDIA = "social_media"
    REFERRALS = "referrals"


class GrowthMetric(StrEnum):
    """Community growth metric types."""

    NEW_VOLUNTEERS = "new_volunteers"
    NEW_DONORS = "new_donors"
    NEW_ADOPTERS = "new_adopters"
    NEW_FOLLOWERS = "new_followers"
    EVENT_ATTENDEES = "event_attendees"


CHANNEL_LABELS_ES: dict[str, str] = {
    EngagementChannel.VOLUNTEERING: "Voluntariado",
    EngagementChannel.DONATIONS: "Donaciones",
    EngagementChannel.ADOPTIONS: "Adopciones",
    EngagementChannel.EVENTS: "Eventos",
    EngagementChannel.SOCIAL_MEDIA: "Redes sociales",
    EngagementChannel.REFERRALS: "Referencias",
}

GROWTH_LABELS_ES: dict[str, str] = {
    GrowthMetric.NEW_VOLUNTEERS: "Nuevos voluntarios",
    GrowthMetric.NEW_DONORS: "Nuevos donantes",
    GrowthMetric.NEW_ADOPTERS: "Nuevos adoptantes",
    GrowthMetric.NEW_FOLLOWERS: "Nuevos seguidores",
    GrowthMetric.EVENT_ATTENDEES: "Asistentes a eventos",
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class EngagementKPI(BaseModel):
    """Key engagement KPI."""

    label: str
    value: int
    change_pct: float
    trend: str = Field(description="up, down, or stable")


class EngagementOverview(BaseModel):
    """Community engagement overview."""

    period_days: int
    total_active_members: int
    engagement_score: float
    kpis: list[EngagementKPI]
    generated_at: str


class VolunteerMetrics(BaseModel):
    """Volunteer activity metrics."""

    total_volunteers: int
    active_this_period: int
    total_hours: float
    avg_hours_per_volunteer: float
    top_activities: list[dict[str, Any]]
    monthly_hours: list[dict[str, Any]]


class EventMetrics(BaseModel):
    """Event participation metrics."""

    total_events: int
    total_attendees: int
    avg_attendance: float
    upcoming_events: int
    events_by_type: list[dict[str, Any]]
    monthly_events: list[dict[str, Any]]


class SocialMetrics(BaseModel):
    """Social media reach metrics."""

    total_followers: int
    total_reach: int
    engagement_rate: float
    platforms: list[dict[str, Any]]
    monthly_reach: list[dict[str, Any]]


class GrowthTrend(BaseModel):
    """Community growth trend data point."""

    month: str
    metric: GrowthMetric
    value: int
    cumulative: int


class CommunityGrowth(BaseModel):
    """Community growth trends."""

    period_days: int
    trends: list[GrowthTrend]
    summary: dict[str, int]


class ChannelEngagement(BaseModel):
    """Engagement score per channel."""

    channel: EngagementChannel
    label: str
    score: float
    active_users: int
    interactions: int
    trend: str


class EngagementBreakdown(BaseModel):
    """Engagement score breakdown by channel."""

    overall_score: float
    channels: list[ChannelEngagement]


# ---------------------------------------------------------------------------
# Sample data generators
# ---------------------------------------------------------------------------


def _generate_overview(period_days: int) -> EngagementOverview:
    """Generate sample engagement overview."""
    return EngagementOverview(
        period_days=period_days,
        total_active_members=247,
        engagement_score=72.5,
        kpis=[
            EngagementKPI(
                label="Voluntarios activos",
                value=45,
                change_pct=12.5,
                trend="up",
            ),
            EngagementKPI(
                label="Donaciones recibidas",
                value=89,
                change_pct=8.3,
                trend="up",
            ),
            EngagementKPI(
                label="Adopciones completadas",
                value=23,
                change_pct=-5.2,
                trend="down",
            ),
            EngagementKPI(
                label="Eventos realizados",
                value=7,
                change_pct=16.7,
                trend="up",
            ),
            EngagementKPI(
                label="Nuevos miembros",
                value=34,
                change_pct=22.1,
                trend="up",
            ),
            EngagementKPI(
                label="Alcance en redes",
                value=15200,
                change_pct=31.4,
                trend="up",
            ),
        ],
        generated_at=datetime.now(UTC).isoformat(),
    )


def _generate_volunteer_metrics() -> VolunteerMetrics:
    """Generate sample volunteer metrics."""
    return VolunteerMetrics(
        total_volunteers=78,
        active_this_period=45,
        total_hours=1250.5,
        avg_hours_per_volunteer=27.8,
        top_activities=[
            {"activity": "Alimentacion", "hours": 380, "volunteers": 25},
            {"activity": "Limpieza", "hours": 290, "volunteers": 20},
            {"activity": "Paseo de animales", "hours": 220, "volunteers": 18},
            {"activity": "Eventos", "hours": 180, "volunteers": 15},
            {"activity": "Transporte", "hours": 120, "volunteers": 8},
        ],
        monthly_hours=[
            {"month": "2025-10", "hours": 180},
            {"month": "2025-11", "hours": 195},
            {"month": "2025-12", "hours": 160},
            {"month": "2026-01", "hours": 210},
            {"month": "2026-02", "hours": 230},
            {"month": "2026-03", "hours": 275},
        ],
    )


def _generate_event_metrics() -> EventMetrics:
    """Generate sample event metrics."""
    return EventMetrics(
        total_events=24,
        total_attendees=1580,
        avg_attendance=65.8,
        upcoming_events=3,
        events_by_type=[
            {"type": "Jornada de adopcion", "count": 8, "attendees": 620},
            {"type": "Campana de esterilizacion", "count": 5, "attendees": 380},
            {"type": "Recaudacion de fondos", "count": 4, "attendees": 280},
            {"type": "Educacion comunitaria", "count": 4, "attendees": 200},
            {"type": "Feria de mascotas", "count": 3, "attendees": 100},
        ],
        monthly_events=[
            {"month": "2025-10", "events": 3, "attendees": 210},
            {"month": "2025-11", "events": 4, "attendees": 260},
            {"month": "2025-12", "events": 2, "attendees": 150},
            {"month": "2026-01", "events": 5, "attendees": 340},
            {"month": "2026-02", "events": 4, "attendees": 280},
            {"month": "2026-03", "events": 6, "attendees": 340},
        ],
    )


def _generate_social_metrics() -> SocialMetrics:
    """Generate sample social media metrics."""
    return SocialMetrics(
        total_followers=8450,
        total_reach=45200,
        engagement_rate=4.2,
        platforms=[
            {
                "platform": "Instagram",
                "followers": 4200,
                "reach": 22000,
                "engagement": 5.1,
            },
            {
                "platform": "Facebook",
                "followers": 3100,
                "reach": 18000,
                "engagement": 3.8,
            },
            {
                "platform": "TikTok",
                "followers": 850,
                "reach": 4200,
                "engagement": 6.2,
            },
            {
                "platform": "Twitter/X",
                "followers": 300,
                "reach": 1000,
                "engagement": 1.5,
            },
        ],
        monthly_reach=[
            {"month": "2025-10", "reach": 5800},
            {"month": "2025-11", "reach": 6200},
            {"month": "2025-12", "reach": 7100},
            {"month": "2026-01", "reach": 8400},
            {"month": "2026-02", "reach": 9200},
            {"month": "2026-03", "reach": 8500},
        ],
    )


def _generate_growth(period_days: int) -> CommunityGrowth:
    """Generate sample community growth data."""
    months = ["2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03"]
    trends: list[GrowthTrend] = []
    cumulative_map: dict[str, int] = {
        GrowthMetric.NEW_VOLUNTEERS: 42,
        GrowthMetric.NEW_DONORS: 65,
        GrowthMetric.NEW_ADOPTERS: 28,
    }
    values_map: dict[str, list[int]] = {
        GrowthMetric.NEW_VOLUNTEERS: [5, 7, 4, 8, 9, 12],
        GrowthMetric.NEW_DONORS: [8, 10, 6, 12, 14, 15],
        GrowthMetric.NEW_ADOPTERS: [3, 4, 2, 5, 4, 6],
    }
    for metric_key in [
        GrowthMetric.NEW_VOLUNTEERS,
        GrowthMetric.NEW_DONORS,
        GrowthMetric.NEW_ADOPTERS,
    ]:
        cumulative = cumulative_map[metric_key]
        for i, month in enumerate(months):
            val = values_map[metric_key][i]
            cumulative += val
            trends.append(
                GrowthTrend(
                    month=month,
                    metric=GrowthMetric(metric_key),
                    value=val,
                    cumulative=cumulative,
                )
            )
    return CommunityGrowth(
        period_days=period_days,
        trends=trends,
        summary={
            "total_new_volunteers": 45,
            "total_new_donors": 65,
            "total_new_adopters": 24,
        },
    )


def _generate_engagement_breakdown() -> EngagementBreakdown:
    """Generate sample engagement breakdown."""
    return EngagementBreakdown(
        overall_score=72.5,
        channels=[
            ChannelEngagement(
                channel=EngagementChannel.VOLUNTEERING,
                label=CHANNEL_LABELS_ES[EngagementChannel.VOLUNTEERING],
                score=82.0,
                active_users=45,
                interactions=1250,
                trend="up",
            ),
            ChannelEngagement(
                channel=EngagementChannel.DONATIONS,
                label=CHANNEL_LABELS_ES[EngagementChannel.DONATIONS],
                score=75.5,
                active_users=89,
                interactions=312,
                trend="up",
            ),
            ChannelEngagement(
                channel=EngagementChannel.ADOPTIONS,
                label=CHANNEL_LABELS_ES[EngagementChannel.ADOPTIONS],
                score=68.0,
                active_users=23,
                interactions=67,
                trend="down",
            ),
            ChannelEngagement(
                channel=EngagementChannel.EVENTS,
                label=CHANNEL_LABELS_ES[EngagementChannel.EVENTS],
                score=71.0,
                active_users=156,
                interactions=580,
                trend="up",
            ),
            ChannelEngagement(
                channel=EngagementChannel.SOCIAL_MEDIA,
                label=CHANNEL_LABELS_ES[EngagementChannel.SOCIAL_MEDIA],
                score=65.0,
                active_users=8450,
                interactions=45200,
                trend="up",
            ),
            ChannelEngagement(
                channel=EngagementChannel.REFERRALS,
                label=CHANNEL_LABELS_ES[EngagementChannel.REFERRALS],
                score=73.5,
                active_users=34,
                interactions=89,
                trend="stable",
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/overview", response_model=EngagementOverview)
async def get_engagement_overview(
    period_days: int = Query(DEFAULT_PERIOD_DAYS, ge=7, le=MAX_PERIOD_DAYS),
) -> EngagementOverview:
    """Get community engagement overview with KPIs."""
    return _generate_overview(period_days)


@router.get("/volunteers", response_model=VolunteerMetrics)
async def get_volunteer_metrics() -> VolunteerMetrics:
    """Get volunteer activity metrics."""
    return _generate_volunteer_metrics()


@router.get("/events", response_model=EventMetrics)
async def get_event_metrics() -> EventMetrics:
    """Get event participation metrics."""
    return _generate_event_metrics()


@router.get("/social", response_model=SocialMetrics)
async def get_social_metrics() -> SocialMetrics:
    """Get social media reach metrics."""
    return _generate_social_metrics()


@router.get("/growth", response_model=CommunityGrowth)
async def get_community_growth(
    period_days: int = Query(DEFAULT_PERIOD_DAYS, ge=7, le=MAX_PERIOD_DAYS),
) -> CommunityGrowth:
    """Get community growth trends."""
    return _generate_growth(period_days)


@router.get("/engagement", response_model=EngagementBreakdown)
async def get_engagement_breakdown() -> EngagementBreakdown:
    """Get engagement score breakdown by channel."""
    return _generate_engagement_breakdown()
