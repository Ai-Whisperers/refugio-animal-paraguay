"""Tests for the donor retention analytics module (RAP-635).

Covers module structure, constants, sample data, API endpoints,
frontend page, accessibility, and app registration.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Module structure
# ---------------------------------------------------------------------------
class TestModuleStructure:
    """Verify module-level attributes and exports."""

    def test_router_exists(self) -> None:
        from src.api.donor_retention_analytics import router

        assert router is not None

    def test_router_prefix(self) -> None:
        from src.api.donor_retention_analytics import router

        assert router.prefix == "/api/admin/analytics/donors"

    def test_router_tag(self) -> None:
        from src.api.donor_retention_analytics import router

        assert "donor-analytics" in router.tags

    def test_donor_segment_enum(self) -> None:
        from src.api.donor_retention_analytics import DonorSegment

        assert hasattr(DonorSegment, "NEW")
        assert hasattr(DonorSegment, "ACTIVE")
        assert hasattr(DonorSegment, "AT_RISK")
        assert hasattr(DonorSegment, "LAPSED")
        assert hasattr(DonorSegment, "CHURNED")

    def test_engagement_level_enum(self) -> None:
        from src.api.donor_retention_analytics import EngagementLevel

        assert hasattr(EngagementLevel, "HIGH")
        assert hasattr(EngagementLevel, "LOW")
        assert hasattr(EngagementLevel, "INACTIVE")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
class TestConstants:
    """Verify named constants."""

    def test_threshold_days(self) -> None:
        from src.api.donor_retention_analytics import (
            ACTIVE_THRESHOLD_DAYS,
            CHURNED_THRESHOLD_DAYS,
            LAPSED_THRESHOLD_DAYS,
        )

        assert ACTIVE_THRESHOLD_DAYS == 90
        assert LAPSED_THRESHOLD_DAYS == 180
        assert CHURNED_THRESHOLD_DAYS == 365

    def test_segment_labels_spanish(self) -> None:
        from src.api.donor_retention_analytics import SEGMENT_LABELS_ES

        assert len(SEGMENT_LABELS_ES) == 5

    def test_engagement_labels_spanish(self) -> None:
        from src.api.donor_retention_analytics import ENGAGEMENT_LABELS_ES

        assert len(ENGAGEMENT_LABELS_ES) == 4


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------
class TestSampleData:
    """Validate sample data structure."""

    def test_acquisition_trends(self) -> None:
        from src.api.donor_retention_analytics import SAMPLE_ACQUISITION_TRENDS

        assert len(SAMPLE_ACQUISITION_TRENDS) == 6

    def test_segments(self) -> None:
        from src.api.donor_retention_analytics import SAMPLE_SEGMENTS

        assert len(SAMPLE_SEGMENTS) == 5

    def test_engagement(self) -> None:
        from src.api.donor_retention_analytics import SAMPLE_ENGAGEMENT

        assert len(SAMPLE_ENGAGEMENT) == 4

    def test_reactivation(self) -> None:
        from src.api.donor_retention_analytics import SAMPLE_REACTIVATION

        assert len(SAMPLE_REACTIVATION) == 8

    def test_segment_percentages_sum(self) -> None:
        from src.api.donor_retention_analytics import SAMPLE_SEGMENTS

        total = sum(s["percentage"] for s in SAMPLE_SEGMENTS)
        assert abs(total - 100.0) < 1.5


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class TestSchemas:
    """Verify schema fields."""

    def test_retention_summary(self) -> None:
        from src.api.donor_retention_analytics import RetentionSummary

        schema = RetentionSummary.model_json_schema()
        props = schema.get("properties", {})
        assert "retention_rate" in props
        assert "churn_rate" in props
        assert "average_ltv_pyg" in props

    def test_recurring_analysis(self) -> None:
        from src.api.donor_retention_analytics import RecurringAnalysis

        schema = RecurringAnalysis.model_json_schema()
        props = schema.get("properties", {})
        assert "recurring_donors" in props
        assert "conversion_rate" in props

    def test_reactivation_opportunity(self) -> None:
        from src.api.donor_retention_analytics import ReactivationOpportunity

        schema = ReactivationOpportunity.model_json_schema()
        props = schema.get("properties", {})
        assert "donor_name" in props
        assert "reactivation_priority" in props


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------
class TestAPIEndpoints:
    """Test API endpoint functions."""

    def test_get_retention_metrics(self) -> None:
        from src.api.donor_retention_analytics import get_retention_metrics

        result = asyncio.get_event_loop().run_until_complete(get_retention_metrics(period_days=30))
        assert result.retention_rate > 0
        assert result.churn_rate > 0
        assert result.retention_rate + result.churn_rate == 100.0
        assert len(result.metrics) == 4

    def test_get_donor_segments(self) -> None:
        from src.api.donor_retention_analytics import get_donor_segments

        result = asyncio.get_event_loop().run_until_complete(get_donor_segments(period_days=30))
        assert len(result) == 5

    def test_get_acquisition_trends(self) -> None:
        from src.api.donor_retention_analytics import get_acquisition_trends

        result = asyncio.get_event_loop().run_until_complete(get_acquisition_trends(months=6))
        assert len(result) == 6

    def test_get_acquisition_trends_limited(self) -> None:
        from src.api.donor_retention_analytics import get_acquisition_trends

        result = asyncio.get_event_loop().run_until_complete(get_acquisition_trends(months=3))
        assert len(result) == 3

    def test_get_recurring_analysis(self) -> None:
        from src.api.donor_retention_analytics import get_recurring_analysis

        result = asyncio.get_event_loop().run_until_complete(get_recurring_analysis(period_days=30))
        assert result.recurring_donors > 0
        assert result.one_time_donors > 0
        assert result.conversion_rate > 0

    def test_get_engagement_scores(self) -> None:
        from src.api.donor_retention_analytics import get_engagement_scores

        result = asyncio.get_event_loop().run_until_complete(get_engagement_scores(period_days=30))
        assert len(result) == 4

    def test_get_reactivation_opportunities(self) -> None:
        from src.api.donor_retention_analytics import get_reactivation_opportunities

        result = asyncio.get_event_loop().run_until_complete(
            get_reactivation_opportunities(limit=10)
        )
        assert len(result) == 8
        # Sorted by priority - critical first
        assert result[0].reactivation_priority == "critical"

    def test_get_reactivation_limited(self) -> None:
        from src.api.donor_retention_analytics import get_reactivation_opportunities

        result = asyncio.get_event_loop().run_until_complete(
            get_reactivation_opportunities(limit=3)
        )
        assert len(result) == 3


# ---------------------------------------------------------------------------
# Frontend page
# ---------------------------------------------------------------------------
class TestDonorAnalyticsPage:
    """Validate the frontend page."""

    @pytest.fixture(autouse=True)
    def _load_page(self) -> None:
        page_path = Path("frontend/src/app/admin/analytics/donantes/page.tsx")
        assert page_path.exists(), "Donor analytics page not found"
        self.content = page_path.read_text()

    def test_is_client_component(self) -> None:
        assert '"use client"' in self.content

    def test_has_page_title(self) -> None:
        assert "Donantes" in self.content

    def test_has_retention_cards(self) -> None:
        assert "RetentionCard" in self.content

    def test_has_segment_chart(self) -> None:
        assert "SegmentChart" in self.content

    def test_has_acquisition_chart(self) -> None:
        assert "AcquisitionChart" in self.content

    def test_has_recurring_section(self) -> None:
        assert "RecurringCard" in self.content

    def test_has_engagement_chart(self) -> None:
        assert "EngagementChart" in self.content

    def test_has_reactivation_table(self) -> None:
        assert "ReactivationTable" in self.content

    def test_has_period_selector(self) -> None:
        assert "periodDays" in self.content

    def test_has_loading_state(self) -> None:
        assert "loading" in self.content.lower()

    def test_has_error_handling(self) -> None:
        assert "error" in self.content.lower()

    def test_has_priority_colors(self) -> None:
        assert "PRIORITY_COLORS" in self.content or "priority" in self.content.lower()


# ---------------------------------------------------------------------------
# Accessibility
# ---------------------------------------------------------------------------
class TestAccessibility:
    """Validate WCAG compliance patterns."""

    @pytest.fixture(autouse=True)
    def _load_page(self) -> None:
        page_path = Path("frontend/src/app/admin/analytics/donantes/page.tsx")
        self.content = page_path.read_text()

    def test_has_aria_labels(self) -> None:
        assert "aria-label" in self.content

    def test_has_role_attributes(self) -> None:
        assert 'role="' in self.content

    def test_has_alert_role(self) -> None:
        assert 'role="alert"' in self.content

    def test_has_list_roles(self) -> None:
        assert 'role="list"' in self.content

    def test_has_region_roles(self) -> None:
        assert 'role="region"' in self.content

    def test_has_aria_busy(self) -> None:
        assert "aria-busy" in self.content

    def test_has_aria_pressed(self) -> None:
        assert "aria-pressed" in self.content

    def test_has_aria_hidden(self) -> None:
        assert 'aria-hidden="true"' in self.content

    def test_has_semantic_headings(self) -> None:
        assert "<h1" in self.content and "<h2" in self.content

    def test_has_min_touch_targets(self) -> None:
        assert "min-h-[44px]" in self.content


# ---------------------------------------------------------------------------
# App registration
# ---------------------------------------------------------------------------
class TestAppRegistration:
    """Verify router is registered."""

    def test_router_imported(self) -> None:
        app_content = Path("src/app.py").read_text()
        assert "donor_retention_analytics_router" in app_content

    def test_router_included(self) -> None:
        app_content = Path("src/app.py").read_text()
        assert "application.include_router(donor_retention_analytics_router)" in app_content
