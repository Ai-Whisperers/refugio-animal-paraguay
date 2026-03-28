"""Tests for RAP-606: Financial transparency dashboard.

Covers the backend API (financial_stats) and frontend page (transparencia).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_FILE = PROJECT_ROOT / "src" / "api" / "financial_stats.py"
FRONTEND_FILE = PROJECT_ROOT / "frontend" / "src" / "app" / "transparencia" / "page.tsx"
APP_FILE = PROJECT_ROOT / "src" / "app.py"


# ---------------------------------------------------------------------------
# Backend: Module structure
# ---------------------------------------------------------------------------


class TestFinancialStatsModule:
    """Verify financial_stats module structure and exports."""

    def test_backend_file_exists(self) -> None:
        assert BACKEND_FILE.exists()

    def test_imports_router(self) -> None:
        from src.api.financial_stats import router

        assert router is not None

    def test_router_prefix(self) -> None:
        from src.api.financial_stats import router

        assert router.prefix == "/api/stats"

    def test_router_tags(self) -> None:
        from src.api.financial_stats import router

        assert "financial-stats" in router.tags

    def test_registered_in_app(self) -> None:
        content = APP_FILE.read_text()
        assert "financial_stats_router" in content
        assert "from src.api.financial_stats import" in content


# ---------------------------------------------------------------------------
# Backend: Constants
# ---------------------------------------------------------------------------


class TestFinancialStatsConstants:
    """Verify constants are properly defined."""

    def test_cache_ttl(self) -> None:
        from src.api.financial_stats import CACHE_TTL_SECONDS

        assert CACHE_TTL_SECONDS == 3600

    def test_pyg_to_usd_rate(self) -> None:
        from src.api.financial_stats import PYG_TO_USD_RATE

        assert 0 < PYG_TO_USD_RATE < 1

    def test_months_history(self) -> None:
        from src.api.financial_stats import MONTHS_HISTORY

        assert MONTHS_HISTORY == 12

    def test_month_names_spanish(self) -> None:
        from src.api.financial_stats import MONTH_NAMES_ES

        assert len(MONTH_NAMES_ES) == 13
        assert MONTH_NAMES_ES[0] == ""
        assert MONTH_NAMES_ES[1] == "Ene"
        assert MONTH_NAMES_ES[12] == "Dic"

    def test_expense_category_labels(self) -> None:
        from src.api.financial_stats import ExpenseCategoryLabel

        assert ExpenseCategoryLabel.MEDICAL.value == "Medico"
        assert ExpenseCategoryLabel.FOOD.value == "Comida"
        assert ExpenseCategoryLabel.SHELTER.value == "Refugio"
        assert ExpenseCategoryLabel.RESCUE.value == "Rescate"
        assert ExpenseCategoryLabel.OPERATIONS.value == "Operaciones"
        assert ExpenseCategoryLabel.TRANSPORT.value == "Transporte"
        assert ExpenseCategoryLabel.ADMINISTRATION.value == "Administracion"


# ---------------------------------------------------------------------------
# Backend: Data generation
# ---------------------------------------------------------------------------


class TestGenerateFinancialStats:
    """Test the generate_financial_stats function."""

    def test_returns_dict(self) -> None:
        from src.api.financial_stats import generate_financial_stats

        result = generate_financial_stats()
        assert isinstance(result, dict)

    def test_has_required_keys(self) -> None:
        from src.api.financial_stats import generate_financial_stats

        result = generate_financial_stats()
        required_keys = {
            "generated_at",
            "cache_ttl_seconds",
            "year",
            "disclaimer_es",
            "metrics",
            "expense_categories",
            "monthly_comparison",
            "last_updated",
        }
        assert required_keys.issubset(result.keys())

    def test_four_metric_cards(self) -> None:
        from src.api.financial_stats import generate_financial_stats

        result = generate_financial_stats()
        assert len(result["metrics"]) == 4

    def test_metric_labels_spanish(self) -> None:
        from src.api.financial_stats import generate_financial_stats

        result = generate_financial_stats()
        labels = [m["label_es"] for m in result["metrics"]]
        assert "Recibido este mes" in labels
        assert "Gastado este mes" in labels
        assert "Recibido este ano" in labels
        assert "Balance disponible" in labels

    def test_metrics_have_pyg_and_usd(self) -> None:
        from src.api.financial_stats import generate_financial_stats

        result = generate_financial_stats()
        for metric in result["metrics"]:
            assert "pyg" in metric["amount"]
            assert "usd" in metric["amount"]

    def test_seven_expense_categories(self) -> None:
        from src.api.financial_stats import generate_financial_stats

        result = generate_financial_stats()
        assert len(result["expense_categories"]) == 7

    def test_category_percentages_sum_to_100(self) -> None:
        from src.api.financial_stats import generate_financial_stats

        result = generate_financial_stats()
        total = sum(c["percentage"] for c in result["expense_categories"])
        assert abs(total - 100.0) < 0.1

    def test_twelve_months_comparison(self) -> None:
        from src.api.financial_stats import generate_financial_stats

        result = generate_financial_stats()
        assert len(result["monthly_comparison"]) == 12

    def test_monthly_has_income_and_expenses(self) -> None:
        from src.api.financial_stats import generate_financial_stats

        result = generate_financial_stats()
        for month in result["monthly_comparison"]:
            assert "income_pyg" in month
            assert "expenses_pyg" in month
            assert "net_pyg" in month
            assert "month_label" in month

    def test_net_equals_income_minus_expenses(self) -> None:
        from src.api.financial_stats import generate_financial_stats

        result = generate_financial_stats()
        for month in result["monthly_comparison"]:
            assert month["net_pyg"] == month["income_pyg"] - month["expenses_pyg"]

    def test_disclaimer_in_spanish(self) -> None:
        from src.api.financial_stats import generate_financial_stats

        result = generate_financial_stats()
        assert "aprobados" in result["disclaimer_es"]
        assert "junta directiva" in result["disclaimer_es"]

    def test_custom_year(self) -> None:
        from src.api.financial_stats import generate_financial_stats

        result = generate_financial_stats(year=2025)
        assert result["year"] == 2025

    def test_pyg_to_usd_conversion(self) -> None:
        from src.api.financial_stats import _pyg_to_usd

        result = _pyg_to_usd(1_000_000)
        assert isinstance(result, float)
        assert result > 0


# ---------------------------------------------------------------------------
# Backend: API endpoint
# ---------------------------------------------------------------------------


class TestFinancialStatsEndpoint:
    """Test the /api/stats/financial endpoint."""

    @pytest.fixture()
    def client(self) -> TestClient:
        from src.app import app

        return TestClient(app)

    def test_get_financial_stats_200(self, client: TestClient) -> None:
        response = client.get("/api/stats/financial")
        assert response.status_code == 200

    def test_response_has_metrics(self, client: TestClient) -> None:
        response = client.get("/api/stats/financial")
        data = response.json()
        assert "metrics" in data
        assert len(data["metrics"]) == 4

    def test_response_has_categories(self, client: TestClient) -> None:
        response = client.get("/api/stats/financial")
        data = response.json()
        assert "expense_categories" in data
        assert len(data["expense_categories"]) == 7

    def test_response_has_monthly(self, client: TestClient) -> None:
        response = client.get("/api/stats/financial")
        data = response.json()
        assert "monthly_comparison" in data
        assert len(data["monthly_comparison"]) == 12

    def test_custom_year_param(self, client: TestClient) -> None:
        response = client.get("/api/stats/financial?year=2025")
        assert response.status_code == 200
        assert response.json()["year"] == 2025

    def test_invalid_year_rejected(self, client: TestClient) -> None:
        response = client.get("/api/stats/financial?year=1999")
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Frontend: Page structure
# ---------------------------------------------------------------------------


class TestTransparenciaPage:
    """Verify the transparency dashboard frontend page."""

    @pytest.fixture(autouse=True)
    def _load_content(self) -> None:
        self.content = FRONTEND_FILE.read_text()

    def test_file_exists(self) -> None:
        assert FRONTEND_FILE.exists()

    def test_is_client_component(self) -> None:
        assert '"use client"' in self.content

    def test_page_title(self) -> None:
        assert "Transparencia Financiera" in self.content

    def test_subtitle_spanish(self) -> None:
        assert "donacion" in self.content

    def test_metric_cards_component(self) -> None:
        assert "MetricCards" in self.content

    def test_category_pie_chart(self) -> None:
        assert "CategoryPieChart" in self.content

    def test_monthly_bar_chart(self) -> None:
        assert "MonthlyBarChart" in self.content

    def test_loading_skeleton(self) -> None:
        assert "LoadingSkeleton" in self.content

    def test_error_state(self) -> None:
        assert "ErrorState" in self.content

    def test_format_pyg_function(self) -> None:
        assert "formatPYG" in self.content

    def test_format_usd_function(self) -> None:
        assert "formatUSD" in self.content

    def test_currency_pyg_format(self) -> None:
        assert '"PYG"' in self.content

    def test_currency_usd_format(self) -> None:
        assert '"USD"' in self.content

    def test_api_fetch(self) -> None:
        assert "/api/stats/financial" in self.content

    def test_disclaimer_display(self) -> None:
        assert "disclaimer_es" in self.content

    def test_last_updated_display(self) -> None:
        assert "last_updated" in self.content

    def test_responsive_grid(self) -> None:
        assert "lg:grid-cols-4" in self.content
        assert "lg:grid-cols-2" in self.content

    def test_category_colors(self) -> None:
        assert "CATEGORY_COLORS" in self.content

    def test_income_expense_colors(self) -> None:
        assert "INCOME_COLOR" in self.content
        assert "EXPENSE_COLOR" in self.content

    def test_refresh_interval(self) -> None:
        assert "REFRESH_INTERVAL_MS" in self.content

    def test_retry_button(self) -> None:
        assert "Reintentar" in self.content

    def test_category_labels_spanish(self) -> None:
        assert "Gastos por Categoria" in self.content
        assert "Ingresos" in self.content

    def test_current_month_breakdown(self) -> None:
        assert "Desglose del Mes Actual" in self.content


# ---------------------------------------------------------------------------
# Frontend: Accessibility
# ---------------------------------------------------------------------------


class TestTransparenciaAccessibility:
    """Verify WCAG compliance."""

    @pytest.fixture(autouse=True)
    def _load_content(self) -> None:
        self.content = FRONTEND_FILE.read_text()

    def test_aria_labels_present(self) -> None:
        assert "aria-label" in self.content

    def test_pie_chart_aria(self) -> None:
        assert "Grafico circular" in self.content

    def test_bar_chart_aria(self) -> None:
        assert "Grafico de barras" in self.content

    def test_role_img_on_charts(self) -> None:
        assert 'role="img"' in self.content

    def test_role_alert_on_error(self) -> None:
        assert 'role="alert"' in self.content

    def test_role_list_on_legend(self) -> None:
        assert 'role="list"' in self.content

    def test_min_touch_target(self) -> None:
        assert "min-h-[44px]" in self.content
        assert "min-w-[44px]" in self.content

    def test_section_landmarks(self) -> None:
        assert "<section" in self.content

    def test_heading_hierarchy(self) -> None:
        assert "<h1" in self.content
        assert "<h2" in self.content
