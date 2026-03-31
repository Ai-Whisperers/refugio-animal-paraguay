"""Unit tests for RAP-610: Annual financial report generation.

Tests cover:
- Report data structures
- Report generation service
- CSV export functions
- API endpoints
"""

from pathlib import Path

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from src.services.annual_report import (
    MONTH_NAMES_ES,
    AnimalOutcomes,
    AnnualReport,
    CampaignSummary,
    CategoryBreakdown,
    DonorMetrics,
    FinancialEfficiency,
    MonthlyBreakdown,
    export_campaigns_csv,
    export_expenses_csv,
    export_monthly_csv,
    export_summary_csv,
    generate_annual_report,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Data structure tests
# ---------------------------------------------------------------------------


class TestDataStructures:
    """Tests for report data structures."""

    def test_monthly_breakdown_net(self) -> None:
        m = MonthlyBreakdown(month=1, month_name="Enero", income_cents=100, expenses_cents=40)
        assert m.net_cents == 60

    def test_monthly_breakdown_negative_net(self) -> None:
        m = MonthlyBreakdown(month=1, month_name="Enero", income_cents=40, expenses_cents=100)
        assert m.net_cents == -60

    def test_category_breakdown_defaults(self) -> None:
        c = CategoryBreakdown(category="food")
        assert c.amount_cents == 0
        assert c.percentage == 0.0

    def test_campaign_summary(self) -> None:
        c = CampaignSummary(campaign_name="Test", total_donations_cents=1000, donor_count=5)
        assert c.campaign_name == "Test"
        assert c.donor_count == 5

    def test_donor_metrics_defaults(self) -> None:
        d = DonorMetrics()
        assert d.total_donors == 0
        assert d.new_donors == 0
        assert d.recurring_donors == 0
        assert d.average_donation_cents == 0

    def test_animal_outcomes_defaults(self) -> None:
        a = AnimalOutcomes()
        assert a.rescued == 0
        assert a.adopted == 0
        assert a.castrated == 0
        assert a.treated == 0

    def test_financial_efficiency_defaults(self) -> None:
        e = FinancialEfficiency()
        assert e.direct_care_percentage == 0.0
        assert e.admin_percentage == 0.0

    def test_annual_report_net_result(self) -> None:
        r = AnnualReport(year=2025, total_income_cents=1000, total_expenses_cents=600)
        assert r.net_result_cents == 400

    def test_annual_report_currency(self) -> None:
        r = AnnualReport(year=2025)
        assert r.currency == "PYG"


# ---------------------------------------------------------------------------
# Report generation tests
# ---------------------------------------------------------------------------


class TestGenerateReport:
    """Tests for generate_annual_report()."""

    def test_returns_annual_report(self) -> None:
        report = generate_annual_report(2025)
        assert isinstance(report, AnnualReport)

    def test_year_is_set(self) -> None:
        report = generate_annual_report(2025)
        assert report.year == 2025

    def test_generated_at_is_set(self) -> None:
        report = generate_annual_report(2025)
        assert report.generated_at != ""

    def test_admin_name_default(self) -> None:
        report = generate_annual_report(2025)
        assert report.generated_by == "Administrador"

    def test_admin_name_custom(self) -> None:
        report = generate_annual_report(2025, admin_name="Maria Lopez")
        assert report.generated_by == "Maria Lopez"

    def test_twelve_months(self) -> None:
        report = generate_annual_report(2025)
        assert len(report.monthly_breakdown) == 12

    def test_months_are_spanish(self) -> None:
        report = generate_annual_report(2025)
        assert report.monthly_breakdown[0].month_name == "Enero"
        assert report.monthly_breakdown[11].month_name == "Diciembre"

    def test_expense_categories_present(self) -> None:
        report = generate_annual_report(2025)
        categories = {c.category for c in report.expense_categories}
        assert "food" in categories
        assert "medical" in categories
        assert "transport" in categories

    def test_income_sources_present(self) -> None:
        report = generate_annual_report(2025)
        assert "campaigns" in report.income_by_source
        assert "general" in report.income_by_source


# ---------------------------------------------------------------------------
# Month names tests
# ---------------------------------------------------------------------------


class TestMonthNames:
    """Tests for Spanish month names."""

    def test_twelve_months_plus_empty(self) -> None:
        assert len(MONTH_NAMES_ES) == 13

    def test_first_entry_empty(self) -> None:
        assert MONTH_NAMES_ES[0] == ""

    def test_january_is_enero(self) -> None:
        assert MONTH_NAMES_ES[1] == "Enero"

    def test_december_is_diciembre(self) -> None:
        assert MONTH_NAMES_ES[12] == "Diciembre"


# ---------------------------------------------------------------------------
# CSV export tests
# ---------------------------------------------------------------------------


class TestCSVExport:
    """Tests for CSV export functions."""

    @pytest.fixture()
    def report(self) -> AnnualReport:
        return generate_annual_report(2025, admin_name="Test Admin")

    def test_summary_csv_contains_year(self, report: AnnualReport) -> None:
        csv_text = export_summary_csv(report)
        assert "2025" in csv_text

    def test_summary_csv_contains_admin(self, report: AnnualReport) -> None:
        csv_text = export_summary_csv(report)
        assert "Test Admin" in csv_text

    def test_summary_csv_contains_resumen(self, report: AnnualReport) -> None:
        csv_text = export_summary_csv(report)
        assert "Resumen Ejecutivo" in csv_text

    def test_summary_csv_contains_donor_metrics(self, report: AnnualReport) -> None:
        csv_text = export_summary_csv(report)
        assert "Total donantes" in csv_text

    def test_expenses_csv_has_header(self, report: AnnualReport) -> None:
        csv_text = export_expenses_csv(report)
        assert "Categoria" in csv_text
        assert "Monto" in csv_text

    def test_expenses_csv_has_categories(self, report: AnnualReport) -> None:
        csv_text = export_expenses_csv(report)
        assert "food" in csv_text
        assert "medical" in csv_text

    def test_monthly_csv_has_header(self, report: AnnualReport) -> None:
        csv_text = export_monthly_csv(report)
        assert "Mes" in csv_text
        assert "Ingresos" in csv_text

    def test_monthly_csv_has_twelve_months(self, report: AnnualReport) -> None:
        csv_text = export_monthly_csv(report)
        assert "Enero" in csv_text
        assert "Diciembre" in csv_text

    def test_campaigns_csv_has_header(self, report: AnnualReport) -> None:
        csv_text = export_campaigns_csv(report)
        assert "Campana" in csv_text


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


class TestAnnualReportsAPI:
    """Tests for annual reports API endpoints."""

    @pytest.fixture()
    def client(self) -> TestClient:
        from src.app import create_app

        app = create_app()
        return TestClient(app)

    def test_generate_report(self, client: TestClient) -> None:
        response = client.post(
            "/api/admin/reports/annual",
            json={"year": 2025, "admin_name": "Test Admin"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["year"] == 2025
        assert data["generated_by"] == "Test Admin"

    def test_generate_report_default_admin(self, client: TestClient) -> None:
        response = client.post(
            "/api/admin/reports/annual",
            json={"year": 2025},
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["generated_by"] == "Administrador"

    def test_reject_invalid_year(self, client: TestClient) -> None:
        response = client.post(
            "/api/admin/reports/annual",
            json={"year": 2019},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_export_summary_csv(self, client: TestClient) -> None:
        response = client.get("/api/admin/reports/annual/2025/csv/summary")
        assert response.status_code == status.HTTP_200_OK
        assert "text/csv" in response.headers["content-type"]
        assert "reporte-anual-2025-resumen.csv" in response.headers.get("content-disposition", "")

    def test_export_expenses_csv(self, client: TestClient) -> None:
        response = client.get("/api/admin/reports/annual/2025/csv/expenses")
        assert response.status_code == status.HTTP_200_OK
        assert "text/csv" in response.headers["content-type"]

    def test_export_monthly_csv(self, client: TestClient) -> None:
        response = client.get("/api/admin/reports/annual/2025/csv/monthly")
        assert response.status_code == status.HTTP_200_OK
        assert "text/csv" in response.headers["content-type"]

    def test_export_campaigns_csv(self, client: TestClient) -> None:
        response = client.get("/api/admin/reports/annual/2025/csv/campaigns")
        assert response.status_code == status.HTTP_200_OK
        assert "text/csv" in response.headers["content-type"]

    def test_available_years(self, client: TestClient) -> None:
        response = client.get("/api/admin/reports/annual/available-years")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "years" in data
        assert len(data["years"]) == 5


# ---------------------------------------------------------------------------
# Module structure tests
# ---------------------------------------------------------------------------


class TestModuleStructure:
    """Tests for file existence and registration."""

    def test_service_exists(self) -> None:
        assert (PROJECT_ROOT / "src" / "services" / "annual_report.py").exists()

    def test_api_exists(self) -> None:
        assert (PROJECT_ROOT / "src" / "api" / "annual_reports.py").exists()

    def test_registered_in_app(self) -> None:
        app_source = (PROJECT_ROOT / "src" / "app.py").read_text()
        assert "annual_reports_router" in app_source
