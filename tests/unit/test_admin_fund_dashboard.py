"""Unit tests for admin fund dashboard schemas.

Tests cover:
  - FundDashboardResponse field validation
  - TargetTypeBreakdown schema
  - TrendingPoint / TrendingResponse schemas
  - Health status determination logic
"""

from src.api.admin_fund_dashboard import (
    FundDashboardResponse,
    TargetTypeBreakdown,
    TrendingPoint,
    TrendingResponse,
)

# ---------------------------------------------------------------------------
# TargetTypeBreakdown
# ---------------------------------------------------------------------------


class TestTargetTypeBreakdown:
    """Validation for target type breakdown schema."""

    def test_basic_breakdown(self) -> None:
        item = TargetTypeBreakdown(
            target_type="animal",
            count=42,
            total_cents=150000,
        )
        assert item.target_type == "animal"
        assert item.count == 42
        assert item.total_cents == 150000

    def test_general_type(self) -> None:
        item = TargetTypeBreakdown(
            target_type="general",
            count=10,
            total_cents=50000,
        )
        assert item.target_type == "general"

    def test_zero_values(self) -> None:
        item = TargetTypeBreakdown(
            target_type="clinic",
            count=0,
            total_cents=0,
        )
        assert item.count == 0
        assert item.total_cents == 0


# ---------------------------------------------------------------------------
# TrendingPoint
# ---------------------------------------------------------------------------


class TestTrendingPoint:
    """Validation for trending data point schema."""

    def test_daily_point(self) -> None:
        point = TrendingPoint(
            period="2026-03-28",
            count=5,
            total_cents=25000,
        )
        assert point.period == "2026-03-28"

    def test_weekly_point(self) -> None:
        point = TrendingPoint(
            period="2026-W13",
            count=30,
            total_cents=180000,
        )
        assert point.period.startswith("2026-W")

    def test_monthly_point(self) -> None:
        point = TrendingPoint(
            period="2026-03",
            count=120,
            total_cents=750000,
        )
        assert point.period == "2026-03"


# ---------------------------------------------------------------------------
# TrendingResponse
# ---------------------------------------------------------------------------


class TestTrendingResponse:
    """Validation for the trending response schema."""

    def test_daily_response(self) -> None:
        resp = TrendingResponse(
            granularity="daily",
            data=[
                TrendingPoint(period="2026-03-27", count=3, total_cents=15000),
                TrendingPoint(period="2026-03-28", count=5, total_cents=25000),
            ],
        )
        assert resp.granularity == "daily"
        assert len(resp.data) == 2

    def test_empty_data(self) -> None:
        resp = TrendingResponse(granularity="monthly", data=[])
        assert len(resp.data) == 0


# ---------------------------------------------------------------------------
# FundDashboardResponse
# ---------------------------------------------------------------------------


class TestFundDashboardResponse:
    """Validation for the full dashboard response schema."""

    def test_healthy_dashboard(self) -> None:
        resp = FundDashboardResponse(
            total_donations_cents=1000000,
            total_allocated_cents=850000,
            unallocated_cents=150000,
            allocation_rate=85.0,
            unallocated_count=5,
            total_expenses=20,
            by_target_type=[
                TargetTypeBreakdown(target_type="general", count=50, total_cents=500000),
                TargetTypeBreakdown(target_type="animal", count=30, total_cents=300000),
            ],
            health_status="healthy",
            health_message="Los fondos se estan asignando adecuadamente.",
            total_donation_count=100,
            pending_allocation_count=5,
        )
        assert resp.allocation_rate == 85.0
        assert resp.health_status == "healthy"
        assert len(resp.by_target_type) == 2

    def test_warning_dashboard(self) -> None:
        resp = FundDashboardResponse(
            total_donations_cents=1000000,
            total_allocated_cents=600000,
            unallocated_cents=400000,
            allocation_rate=60.0,
            unallocated_count=15,
            total_expenses=10,
            by_target_type=[],
            health_status="warning",
            health_message="Tasa actual: 60.0%",
            total_donation_count=50,
            pending_allocation_count=15,
        )
        assert resp.health_status == "warning"
        assert resp.unallocated_cents == 400000

    def test_critical_dashboard(self) -> None:
        resp = FundDashboardResponse(
            total_donations_cents=1000000,
            total_allocated_cents=100000,
            unallocated_cents=900000,
            allocation_rate=10.0,
            unallocated_count=40,
            total_expenses=2,
            by_target_type=[],
            health_status="critical",
            health_message="Mas del 90% no asignado.",
            total_donation_count=45,
            pending_allocation_count=40,
        )
        assert resp.health_status == "critical"

    def test_empty_dashboard(self) -> None:
        resp = FundDashboardResponse(
            total_donations_cents=0,
            total_allocated_cents=0,
            unallocated_cents=0,
            allocation_rate=0.0,
            unallocated_count=0,
            total_expenses=0,
            by_target_type=[],
            health_status="critical",
            health_message="No hay donaciones.",
            total_donation_count=0,
            pending_allocation_count=0,
        )
        assert resp.total_donation_count == 0

    def test_all_target_types(self) -> None:
        types = ["general", "animal", "rescuer", "clinic", "campaign", "need"]
        breakdowns = [
            TargetTypeBreakdown(target_type=t, count=i + 1, total_cents=(i + 1) * 10000)
            for i, t in enumerate(types)
        ]
        resp = FundDashboardResponse(
            total_donations_cents=210000,
            total_allocated_cents=200000,
            unallocated_cents=10000,
            allocation_rate=95.2,
            unallocated_count=1,
            total_expenses=6,
            by_target_type=breakdowns,
            health_status="healthy",
            health_message="OK",
            total_donation_count=21,
            pending_allocation_count=1,
        )
        assert len(resp.by_target_type) == 6
