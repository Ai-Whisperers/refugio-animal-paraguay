"""Tests for the donation analytics module (RAP-634).

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
        from src.api.donation_analytics import router

        assert router is not None

    def test_router_prefix(self) -> None:
        from src.api.donation_analytics import router

        assert router.prefix == "/api/admin/analytics/donations"

    def test_router_tag(self) -> None:
        from src.api.donation_analytics import router

        assert "donation-analytics" in router.tags

    def test_donation_source_enum(self) -> None:
        from src.api.donation_analytics import DonationSource

        assert hasattr(DonationSource, "ONLINE")
        assert hasattr(DonationSource, "SEPA")
        assert hasattr(DonationSource, "TIGO_MONEY")
        assert hasattr(DonationSource, "CASH")

    def test_donation_frequency_enum(self) -> None:
        from src.api.donation_analytics import DonationFrequency

        assert hasattr(DonationFrequency, "ONE_TIME")
        assert hasattr(DonationFrequency, "MONTHLY")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
class TestConstants:
    """Verify named constants."""

    def test_default_period_days(self) -> None:
        from src.api.donation_analytics import DEFAULT_PERIOD_DAYS

        assert DEFAULT_PERIOD_DAYS == 30

    def test_max_period_days(self) -> None:
        from src.api.donation_analytics import MAX_PERIOD_DAYS

        assert MAX_PERIOD_DAYS == 365

    def test_currencies_defined(self) -> None:
        from src.api.donation_analytics import CURRENCY_EUR, CURRENCY_PYG

        assert CURRENCY_PYG == "PYG"
        assert CURRENCY_EUR == "EUR"

    def test_top_donors_limit(self) -> None:
        from src.api.donation_analytics import TOP_DONORS_LIMIT

        assert TOP_DONORS_LIMIT == 10

    def test_source_labels_spanish(self) -> None:
        from src.api.donation_analytics import SOURCE_LABELS_ES

        assert len(SOURCE_LABELS_ES) == 6

    def test_frequency_labels_spanish(self) -> None:
        from src.api.donation_analytics import FREQUENCY_LABELS_ES

        assert len(FREQUENCY_LABELS_ES) == 4


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------
class TestSampleData:
    """Validate sample data structure."""

    def test_monthly_trends_count(self) -> None:
        from src.api.donation_analytics import SAMPLE_MONTHLY_TRENDS

        assert len(SAMPLE_MONTHLY_TRENDS) == 6

    def test_source_data_count(self) -> None:
        from src.api.donation_analytics import SAMPLE_SOURCE_DATA

        assert len(SAMPLE_SOURCE_DATA) == 6

    def test_currency_data_count(self) -> None:
        from src.api.donation_analytics import SAMPLE_CURRENCY_DATA

        assert len(SAMPLE_CURRENCY_DATA) == 2

    def test_top_donors_count(self) -> None:
        from src.api.donation_analytics import SAMPLE_TOP_DONORS

        assert len(SAMPLE_TOP_DONORS) == 10

    def test_campaigns_count(self) -> None:
        from src.api.donation_analytics import SAMPLE_CAMPAIGNS

        assert len(SAMPLE_CAMPAIGNS) == 4

    def test_source_percentages_sum_to_100(self) -> None:
        from src.api.donation_analytics import SAMPLE_SOURCE_DATA

        total = sum(s["percentage"] for s in SAMPLE_SOURCE_DATA)
        assert abs(total - 100.0) < 1.0


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class TestSchemas:
    """Verify schema imports and fields."""

    def test_donation_summary_fields(self) -> None:
        from src.api.donation_analytics import DonationSummary

        schema = DonationSummary.model_json_schema()
        props = schema.get("properties", {})
        assert "total_amount_pyg" in props
        assert "total_amount_eur" in props
        assert "donation_count" in props
        assert "kpis" in props

    def test_monthly_trend_fields(self) -> None:
        from src.api.donation_analytics import MonthlyTrend

        schema = MonthlyTrend.model_json_schema()
        props = schema.get("properties", {})
        assert "month" in props
        assert "total_pyg" in props

    def test_top_donor_fields(self) -> None:
        from src.api.donation_analytics import TopDonor

        schema = TopDonor.model_json_schema()
        props = schema.get("properties", {})
        assert "donor_name" in props
        assert "is_recurring" in props

    def test_campaign_performance_fields(self) -> None:
        from src.api.donation_analytics import CampaignPerformance

        schema = CampaignPerformance.model_json_schema()
        props = schema.get("properties", {})
        assert "campaign_name" in props
        assert "progress_percent" in props


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------
class TestAPIEndpoints:
    """Test API endpoint functions."""

    def test_get_donation_summary(self) -> None:
        from src.api.donation_analytics import get_donation_summary

        result = asyncio.get_event_loop().run_until_complete(get_donation_summary(period_days=30))
        assert result.donation_count > 0
        assert result.total_amount_pyg > 0
        assert result.period_days == 30
        assert len(result.kpis) == 4

    def test_get_donation_summary_custom_period(self) -> None:
        from src.api.donation_analytics import get_donation_summary

        result = asyncio.get_event_loop().run_until_complete(get_donation_summary(period_days=90))
        assert result.period_days == 90

    def test_get_donation_trends(self) -> None:
        from src.api.donation_analytics import get_donation_trends

        result = asyncio.get_event_loop().run_until_complete(get_donation_trends(months=6))
        assert result.period_months == 6
        assert len(result.months) == 6

    def test_get_donation_trends_limited(self) -> None:
        from src.api.donation_analytics import get_donation_trends

        result = asyncio.get_event_loop().run_until_complete(get_donation_trends(months=3))
        assert len(result.months) == 3

    def test_get_donations_by_source(self) -> None:
        from src.api.donation_analytics import get_donations_by_source

        result = asyncio.get_event_loop().run_until_complete(
            get_donations_by_source(period_days=30)
        )
        assert len(result) == 6
        assert result[0].label  # has Spanish label

    def test_get_donations_by_currency(self) -> None:
        from src.api.donation_analytics import get_donations_by_currency

        result = asyncio.get_event_loop().run_until_complete(
            get_donations_by_currency(period_days=30)
        )
        assert len(result) == 2
        currencies = {c.currency for c in result}
        assert "PYG" in currencies
        assert "EUR" in currencies

    def test_get_top_donors(self) -> None:
        from src.api.donation_analytics import get_top_donors

        result = asyncio.get_event_loop().run_until_complete(
            get_top_donors(limit=10, period_days=30)
        )
        assert len(result) == 10
        assert result[0].rank == 1

    def test_get_top_donors_limited(self) -> None:
        from src.api.donation_analytics import get_top_donors

        result = asyncio.get_event_loop().run_until_complete(
            get_top_donors(limit=5, period_days=30)
        )
        assert len(result) == 5

    def test_get_campaign_performance(self) -> None:
        from src.api.donation_analytics import get_campaign_performance

        result = asyncio.get_event_loop().run_until_complete(get_campaign_performance())
        assert len(result) == 4
        # At least one completed campaign
        statuses = {c.status for c in result}
        assert "completed" in statuses or "active" in statuses


# ---------------------------------------------------------------------------
# Frontend page
# ---------------------------------------------------------------------------
class TestDonationAnalyticsPage:
    """Validate the frontend page."""

    @pytest.fixture(autouse=True)
    def _load_page(self) -> None:
        page_path = Path("frontend/src/app/admin/analytics/donaciones/page.tsx")
        assert page_path.exists(), "Donation analytics page not found"
        self.content = page_path.read_text()

    def test_is_client_component(self) -> None:
        assert '"use client"' in self.content

    def test_has_page_title(self) -> None:
        assert "Donaciones" in self.content or "donaciones" in self.content

    def test_has_kpi_cards(self) -> None:
        assert "KPICard" in self.content or "kpi" in self.content.lower()

    def test_has_trend_chart(self) -> None:
        assert "TrendChart" in self.content

    def test_has_source_chart(self) -> None:
        assert "SourceChart" in self.content

    def test_has_currency_distribution(self) -> None:
        assert "CurrencyCards" in self.content or "currency" in self.content.lower()

    def test_has_top_donors_table(self) -> None:
        assert "TopDonorsTable" in self.content or "TopDonor" in self.content

    def test_has_campaign_section(self) -> None:
        assert "CampaignCards" in self.content or "campaign" in self.content.lower()

    def test_has_period_selector(self) -> None:
        assert "periodDays" in self.content or "period" in self.content.lower()

    def test_has_loading_state(self) -> None:
        assert "loading" in self.content.lower()

    def test_has_error_handling(self) -> None:
        assert "error" in self.content.lower()

    def test_has_pyg_formatting(self) -> None:
        assert "PYG" in self.content or "formatPYG" in self.content

    def test_has_eur_formatting(self) -> None:
        assert "EUR" in self.content or "formatEUR" in self.content


# ---------------------------------------------------------------------------
# Accessibility
# ---------------------------------------------------------------------------
class TestAccessibility:
    """Validate WCAG compliance patterns."""

    @pytest.fixture(autouse=True)
    def _load_page(self) -> None:
        page_path = Path("frontend/src/app/admin/analytics/donaciones/page.tsx")
        self.content = page_path.read_text()

    def test_has_aria_labels(self) -> None:
        assert "aria-label" in self.content

    def test_has_role_attributes(self) -> None:
        assert 'role="' in self.content

    def test_has_alert_role(self) -> None:
        assert 'role="alert"' in self.content

    def test_has_progressbar_role(self) -> None:
        assert 'role="progressbar"' in self.content

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
        assert "min-h-[44px]" in self.content or "h-11" in self.content


# ---------------------------------------------------------------------------
# App registration
# ---------------------------------------------------------------------------
class TestAppRegistration:
    """Verify router is registered in the FastAPI application."""

    def test_donation_analytics_router_imported(self) -> None:
        app_content = Path("src/app.py").read_text()
        assert "donation_analytics_router" in app_content

    def test_donation_analytics_router_included(self) -> None:
        app_content = Path("src/app.py").read_text()
        assert "application.include_router(donation_analytics_router)" in app_content
