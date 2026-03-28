"""Tests for executive KPI dashboard API."""

import pytest
from src.api.executive_kpi_dashboard import (
    CATEGORY_LABELS_ES,
    DEFAULT_PERIOD_DAYS,
    KPI_TARGET_ADOPTION_RATE,
    KPI_TARGET_DONOR_RETENTION,
    KPI_TARGET_LIVE_RELEASE,
    KPI_TARGET_LOS_DAYS,
    MAX_PERIOD_DAYS,
    SEVERITY_LABELS_ES,
    AlertSeverity,
    KPICategory,
    TrendDirection,
    get_dashboard_alerts,
    get_financial_summary,
    get_kpi_dashboard,
    get_operational_metrics,
    get_performance_scorecard,
    router,
)

# ---------------------------------------------------------------------------
# Enum tests
# ---------------------------------------------------------------------------


class TestEnums:
    """Verify enum members and labels."""

    def test_kpi_category_members(self) -> None:
        assert set(KPICategory) == {
            KPICategory.ANIMALS,
            KPICategory.FINANCIAL,
            KPICategory.OPERATIONS,
            KPICategory.COMMUNITY,
        }

    def test_alert_severity_members(self) -> None:
        assert set(AlertSeverity) == {
            AlertSeverity.CRITICAL,
            AlertSeverity.WARNING,
            AlertSeverity.INFO,
        }

    def test_trend_direction_members(self) -> None:
        assert set(TrendDirection) == {
            TrendDirection.UP,
            TrendDirection.DOWN,
            TrendDirection.STABLE,
        }

    def test_category_labels_cover_all(self) -> None:
        for c in KPICategory:
            assert c.value in CATEGORY_LABELS_ES

    def test_severity_labels_cover_all(self) -> None:
        for s in AlertSeverity:
            assert s.value in SEVERITY_LABELS_ES


# ---------------------------------------------------------------------------
# Constants tests
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify constant values."""

    def test_default_period(self) -> None:
        assert DEFAULT_PERIOD_DAYS == 30

    def test_max_period(self) -> None:
        assert MAX_PERIOD_DAYS == 365

    def test_adoption_target(self) -> None:
        assert KPI_TARGET_ADOPTION_RATE == 70.0

    def test_live_release_target(self) -> None:
        assert KPI_TARGET_LIVE_RELEASE == 90.0

    def test_los_target(self) -> None:
        assert KPI_TARGET_LOS_DAYS == 20

    def test_donor_retention_target(self) -> None:
        assert KPI_TARGET_DONOR_RETENTION == 60.0


# ---------------------------------------------------------------------------
# Router config tests
# ---------------------------------------------------------------------------


class TestRouterConfig:
    """Verify router setup."""

    def test_router_prefix(self) -> None:
        assert router.prefix == "/api/admin/dashboard"

    def test_router_tags(self) -> None:
        assert "executive-dashboard" in router.tags


# ---------------------------------------------------------------------------
# KPI Dashboard tests
# ---------------------------------------------------------------------------


class TestKPIDashboard:
    """Test GET /kpis endpoint."""

    @pytest.mark.asyncio
    async def test_default_period(self) -> None:
        result = await get_kpi_dashboard(period_days=DEFAULT_PERIOD_DAYS)
        assert result.period_days == DEFAULT_PERIOD_DAYS

    @pytest.mark.asyncio
    async def test_has_kpis(self) -> None:
        result = await get_kpi_dashboard(period_days=30)
        assert len(result.kpis) > 0

    @pytest.mark.asyncio
    async def test_kpis_have_required_fields(self) -> None:
        result = await get_kpi_dashboard(period_days=30)
        for kpi in result.kpis:
            assert kpi.id
            assert kpi.name
            assert kpi.category in KPICategory
            assert kpi.unit

    @pytest.mark.asyncio
    async def test_summary_present(self) -> None:
        result = await get_kpi_dashboard(period_days=30)
        assert "total_kpis" in result.summary
        assert "on_track" in result.summary
        assert "health_score" in result.summary

    @pytest.mark.asyncio
    async def test_summary_counts_match(self) -> None:
        result = await get_kpi_dashboard(period_days=30)
        total = (
            result.summary["on_track"] + result.summary["approaching"] + result.summary["at_risk"]
        )
        assert total == result.summary["total_kpis"]

    @pytest.mark.asyncio
    async def test_generated_at_present(self) -> None:
        result = await get_kpi_dashboard(period_days=30)
        assert result.generated_at is not None

    @pytest.mark.asyncio
    async def test_multiple_categories(self) -> None:
        result = await get_kpi_dashboard(period_days=30)
        categories = {k.category for k in result.kpis}
        assert len(categories) >= 3


# ---------------------------------------------------------------------------
# Financial summary tests
# ---------------------------------------------------------------------------


class TestFinancialSummary:
    """Test GET /financial endpoint."""

    @pytest.mark.asyncio
    async def test_default_period(self) -> None:
        result = await get_financial_summary(period_days=DEFAULT_PERIOD_DAYS)
        assert result.period_days == DEFAULT_PERIOD_DAYS

    @pytest.mark.asyncio
    async def test_income_positive(self) -> None:
        result = await get_financial_summary(period_days=30)
        assert result.total_income_pyg > 0
        assert result.total_income_eur > 0

    @pytest.mark.asyncio
    async def test_expenses_positive(self) -> None:
        result = await get_financial_summary(period_days=30)
        assert result.total_expenses_pyg > 0

    @pytest.mark.asyncio
    async def test_has_campaigns(self) -> None:
        result = await get_financial_summary(period_days=30)
        assert len(result.top_campaigns) > 0

    @pytest.mark.asyncio
    async def test_has_monthly_revenue(self) -> None:
        result = await get_financial_summary(period_days=30)
        assert len(result.monthly_revenue) > 0

    @pytest.mark.asyncio
    async def test_has_expense_breakdown(self) -> None:
        result = await get_financial_summary(period_days=30)
        assert len(result.expense_breakdown) > 0

    @pytest.mark.asyncio
    async def test_donation_count_positive(self) -> None:
        result = await get_financial_summary(period_days=30)
        assert result.donation_count > 0


# ---------------------------------------------------------------------------
# Operational metrics tests
# ---------------------------------------------------------------------------


class TestOperationalMetrics:
    """Test GET /operational endpoint."""

    @pytest.mark.asyncio
    async def test_population_positive(self) -> None:
        result = await get_operational_metrics(period_days=30)
        assert result.current_population > 0

    @pytest.mark.asyncio
    async def test_capacity_valid(self) -> None:
        result = await get_operational_metrics(period_days=30)
        assert 0 < result.capacity_pct <= 100

    @pytest.mark.asyncio
    async def test_rates_valid(self) -> None:
        result = await get_operational_metrics(period_days=30)
        assert 0 <= result.adoption_rate_pct <= 100
        assert 0 <= result.live_release_rate_pct <= 100

    @pytest.mark.asyncio
    async def test_volunteers_positive(self) -> None:
        result = await get_operational_metrics(period_days=30)
        assert result.active_volunteers > 0
        assert result.volunteer_hours > 0


# ---------------------------------------------------------------------------
# Performance scorecard tests
# ---------------------------------------------------------------------------


class TestPerformanceScorecard:
    """Test GET /performance endpoint."""

    @pytest.mark.asyncio
    async def test_has_scores(self) -> None:
        result = await get_performance_scorecard(period_days=30)
        assert len(result.scores) > 0

    @pytest.mark.asyncio
    async def test_overall_score_valid(self) -> None:
        result = await get_performance_scorecard(period_days=30)
        assert result.overall_score > 0

    @pytest.mark.asyncio
    async def test_overall_grade_present(self) -> None:
        result = await get_performance_scorecard(period_days=30)
        assert result.overall_grade in ("A+", "A", "B", "C")

    @pytest.mark.asyncio
    async def test_scores_have_targets(self) -> None:
        result = await get_performance_scorecard(period_days=30)
        for s in result.scores:
            assert "target" in s
            assert "actual" in s
            assert "grade" in s


# ---------------------------------------------------------------------------
# Alerts tests
# ---------------------------------------------------------------------------


class TestDashboardAlerts:
    """Test GET /alerts endpoint."""

    @pytest.mark.asyncio
    async def test_has_alerts(self) -> None:
        result = await get_dashboard_alerts()
        assert result.total > 0

    @pytest.mark.asyncio
    async def test_alerts_have_required_fields(self) -> None:
        result = await get_dashboard_alerts()
        for alert in result.alerts:
            assert alert.id
            assert alert.title
            assert alert.message
            assert alert.severity in AlertSeverity
            assert alert.category in KPICategory

    @pytest.mark.asyncio
    async def test_severity_counts(self) -> None:
        result = await get_dashboard_alerts()
        critical = sum(1 for a in result.alerts if a.severity == AlertSeverity.CRITICAL)
        warning = sum(1 for a in result.alerts if a.severity == AlertSeverity.WARNING)
        assert result.critical_count == critical
        assert result.warning_count == warning

    @pytest.mark.asyncio
    async def test_has_critical_alert(self) -> None:
        result = await get_dashboard_alerts()
        assert result.critical_count >= 1


# ---------------------------------------------------------------------------
# Frontend file assertions
# ---------------------------------------------------------------------------


class TestFrontendFile:
    """Verify frontend page exists."""

    def test_page_file_exists(self) -> None:
        from pathlib import Path

        page = Path("frontend/src/app/admin/dashboard/page.tsx")
        assert page.exists(), "Frontend page must exist"
        content = page.read_text()
        assert "ExecutiveDashboardPage" in content
        assert "Dashboard ejecutivo" in content
