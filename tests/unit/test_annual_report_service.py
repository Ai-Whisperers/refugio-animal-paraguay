"""Unit tests for the annual_report service (RAP-268).

Tests cover:
- Placeholder report generation (backward compat)
- DB-backed async generation
- CSV export helpers
- Monthly breakdown structure
- Donor metrics and animal outcomes
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SERVICE_FILE = PROJECT_ROOT / "src" / "services" / "annual_report.py"
API_FILE = PROJECT_ROOT / "src" / "api" / "annual_reports.py"


# ---------------------------------------------------------------------------
# Module structure
# ---------------------------------------------------------------------------


class TestModuleStructure:
    def test_service_file_exists(self) -> None:
        assert SERVICE_FILE.exists()

    def test_api_file_exists(self) -> None:
        assert API_FILE.exists()

    def test_generate_annual_report_from_db_exported(self) -> None:
        from src.services.annual_report import generate_annual_report_from_db

        assert callable(generate_annual_report_from_db)

    def test_generate_annual_report_sync_still_exported(self) -> None:
        from src.services.annual_report import generate_annual_report

        assert callable(generate_annual_report)


# ---------------------------------------------------------------------------
# Placeholder report (backward compat)
# ---------------------------------------------------------------------------


class TestGenerateAnnualReportSync:
    def test_returns_annual_report_for_year(self) -> None:
        from src.services.annual_report import generate_annual_report

        report = generate_annual_report(2025)
        assert report.year == 2025

    def test_generated_by_default(self) -> None:
        from src.services.annual_report import generate_annual_report

        report = generate_annual_report(2025)
        assert report.generated_by == "Administrador"

    def test_generated_by_custom(self) -> None:
        from src.services.annual_report import generate_annual_report

        report = generate_annual_report(2025, admin_name="Maria")
        assert report.generated_by == "Maria"

    def test_generates_12_monthly_entries(self) -> None:
        from src.services.annual_report import generate_annual_report

        report = generate_annual_report(2025)
        assert len(report.monthly_breakdown) == 12

    def test_monthly_months_sequential(self) -> None:
        from src.services.annual_report import generate_annual_report

        report = generate_annual_report(2025)
        months = [m.month for m in report.monthly_breakdown]
        assert months == list(range(1, 13))

    def test_monthly_names_not_empty(self) -> None:
        from src.services.annual_report import generate_annual_report

        report = generate_annual_report(2025)
        for m in report.monthly_breakdown:
            assert m.month_name, f"Month {m.month} has no name"

    def test_expense_categories_initialized(self) -> None:
        from src.services.annual_report import generate_annual_report

        report = generate_annual_report(2025)
        assert len(report.expense_categories) > 0

    def test_income_by_source_has_keys(self) -> None:
        from src.services.annual_report import generate_annual_report

        report = generate_annual_report(2025)
        assert "general" in report.income_by_source

    def test_net_result_property(self) -> None:
        from src.services.annual_report import AnnualReport

        r = AnnualReport(year=2025, total_income_cents=500, total_expenses_cents=300)
        assert r.net_result_cents == 200

    def test_net_result_negative(self) -> None:
        from src.services.annual_report import AnnualReport

        r = AnnualReport(year=2025, total_income_cents=100, total_expenses_cents=400)
        assert r.net_result_cents == -300

    def test_generated_at_is_recent(self) -> None:
        from src.services.annual_report import generate_annual_report

        before = datetime.now(tz=UTC)
        report = generate_annual_report(2025)
        after = datetime.now(tz=UTC)
        generated = datetime.fromisoformat(report.generated_at)
        # Ensure it's timezone aware before comparison
        if generated.tzinfo is None:
            generated = generated.replace(tzinfo=UTC)
        assert before <= generated <= after


# ---------------------------------------------------------------------------
# DB-backed report
# ---------------------------------------------------------------------------


class TestGenerateAnnualReportFromDB:
    """Test generate_annual_report_from_db with a mocked AsyncSession."""

    def _make_db(self) -> AsyncMock:
        """Build a minimal AsyncSession mock that returns empty query results."""
        db = AsyncMock()

        empty_result = MagicMock()
        empty_result.all.return_value = []
        empty_result.scalar.return_value = None
        empty_result.scalar_one.return_value = 0

        db.execute = AsyncMock(return_value=empty_result)
        return db

    @pytest.mark.asyncio
    async def test_returns_report_for_year(self) -> None:
        from src.services.annual_report import generate_annual_report_from_db

        db = self._make_db()
        report = await generate_annual_report_from_db(db, 2025)
        assert report.year == 2025

    @pytest.mark.asyncio
    async def test_generates_12_monthly_entries(self) -> None:
        from src.services.annual_report import generate_annual_report_from_db

        db = self._make_db()
        report = await generate_annual_report_from_db(db, 2025)
        assert len(report.monthly_breakdown) == 12

    @pytest.mark.asyncio
    async def test_monthly_months_are_sequential(self) -> None:
        from src.services.annual_report import generate_annual_report_from_db

        db = self._make_db()
        report = await generate_annual_report_from_db(db, 2025)
        months = [m.month for m in report.monthly_breakdown]
        assert months == list(range(1, 13))

    @pytest.mark.asyncio
    async def test_zero_income_on_empty_db(self) -> None:
        from src.services.annual_report import generate_annual_report_from_db

        db = self._make_db()
        report = await generate_annual_report_from_db(db, 2025)
        assert report.total_income_cents == 0

    @pytest.mark.asyncio
    async def test_zero_expenses_on_empty_db(self) -> None:
        from src.services.annual_report import generate_annual_report_from_db

        db = self._make_db()
        report = await generate_annual_report_from_db(db, 2025)
        assert report.total_expenses_cents == 0

    @pytest.mark.asyncio
    async def test_donor_metrics_zeroed_on_empty_db(self) -> None:
        from src.services.annual_report import generate_annual_report_from_db

        db = self._make_db()
        report = await generate_annual_report_from_db(db, 2025)
        assert report.donor_metrics.total_donors == 0
        assert report.donor_metrics.new_donors == 0

    @pytest.mark.asyncio
    async def test_animal_outcomes_zeroed_on_empty_db(self) -> None:
        from src.services.annual_report import generate_annual_report_from_db

        db = self._make_db()
        report = await generate_annual_report_from_db(db, 2025)
        assert report.animal_outcomes.rescued == 0
        assert report.animal_outcomes.adopted == 0

    @pytest.mark.asyncio
    async def test_admin_name_propagated(self) -> None:
        from src.services.annual_report import generate_annual_report_from_db

        db = self._make_db()
        report = await generate_annual_report_from_db(db, 2025, admin_name="Carlos")
        assert report.generated_by == "Carlos"

    @pytest.mark.asyncio
    async def test_default_expense_categories_present(self) -> None:
        from src.services.annual_report import generate_annual_report_from_db

        db = self._make_db()
        report = await generate_annual_report_from_db(db, 2025)
        assert len(report.expense_categories) > 0

    @pytest.mark.asyncio
    async def test_efficiency_zero_when_no_income(self) -> None:
        from src.services.annual_report import generate_annual_report_from_db

        db = self._make_db()
        report = await generate_annual_report_from_db(db, 2025)
        # When income is 0, efficiency block is skipped — defaults remain 0
        assert report.efficiency.direct_care_percentage == 0.0
        assert report.efficiency.admin_percentage == 0.0


# ---------------------------------------------------------------------------
# CSV export helpers
# ---------------------------------------------------------------------------


class TestCSVExports:
    def _make_report(self, year: int = 2025):
        from src.services.annual_report import (
            AnnualReport,
            AnimalOutcomes,
            CategoryBreakdown,
            CampaignSummary,
            DonorMetrics,
            FinancialEfficiency,
            MonthlyBreakdown,
        )

        report = AnnualReport(year=year, generated_at="2025-01-01T00:00:00", generated_by="Test")
        report.total_income_cents = 1_000_000
        report.total_expenses_cents = 800_000
        report.income_by_source = {"general": 500_000, "campaigns": 500_000}
        report.monthly_breakdown = [
            MonthlyBreakdown(
                month=m, month_name=f"Mes{m}", income_cents=100_000, expenses_cents=80_000
            )
            for m in range(1, 13)
        ]
        report.expense_categories = [
            CategoryBreakdown(category="food", amount_cents=400_000, percentage=50.0),
            CategoryBreakdown(category="medical", amount_cents=400_000, percentage=50.0),
        ]
        report.top_campaigns = [
            CampaignSummary(
                campaign_name="Esterilizacion", total_donations_cents=200_000, donor_count=10
            )
        ]
        report.donor_metrics = DonorMetrics(
            total_donors=50, new_donors=10, recurring_donors=15, average_donation_cents=20_000
        )
        report.animal_outcomes = AnimalOutcomes(rescued=20, adopted=15)
        report.efficiency = FinancialEfficiency(direct_care_percentage=75.0, admin_percentage=5.0)
        return report

    def test_export_summary_csv_contains_year(self) -> None:
        from src.services.annual_report import export_summary_csv

        csv = export_summary_csv(self._make_report(2025))
        assert "2025" in csv

    def test_export_summary_csv_contains_income(self) -> None:
        from src.services.annual_report import export_summary_csv

        csv = export_summary_csv(self._make_report())
        assert "1000000" in csv

    def test_export_expenses_csv_contains_food(self) -> None:
        from src.services.annual_report import export_expenses_csv

        csv = export_expenses_csv(self._make_report())
        assert "food" in csv

    def test_export_monthly_csv_contains_12_data_rows(self) -> None:
        from src.services.annual_report import export_monthly_csv

        csv_text = export_monthly_csv(self._make_report())
        # All lines that have month data (not header)
        lines = [line for line in csv_text.strip().split("\n") if "Mes" in line and "," in line]
        # Header row "Mes,Ingresos..." also contains "Mes"; filter it out
        data_rows = [line for line in lines if not line.startswith("Mes,")]
        assert len(data_rows) == 12

    def test_export_campaigns_csv_contains_campaign_name(self) -> None:
        from src.services.annual_report import export_campaigns_csv

        csv = export_campaigns_csv(self._make_report())
        assert "Esterilizacion" in csv


# ---------------------------------------------------------------------------
# API router structure
# ---------------------------------------------------------------------------


class TestAnnualReportsRouter:
    def test_router_prefix(self) -> None:
        from src.api.annual_reports import router

        assert router.prefix == "/api/admin/reports"

    def test_router_tags(self) -> None:
        from src.api.annual_reports import router

        assert "annual-reports" in router.tags

    def test_generate_report_endpoint_exists(self) -> None:
        from src.api.annual_reports import router

        paths = [getattr(r, "path", "") for r in router.routes]
        assert any(p.endswith("/annual") for p in paths)

    def test_available_years_endpoint_exists(self) -> None:
        from src.api.annual_reports import router

        paths = [getattr(r, "path", "") for r in router.routes]
        assert any("available-years" in p for p in paths)
