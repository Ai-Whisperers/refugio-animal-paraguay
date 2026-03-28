"""Tests for predictive analytics and forecasting API."""

from typing import Any

import pytest

from src.api.predictive_analytics import (
    AnimalCategory,
    ConfidenceLevel,
    ForecastPoint,
    ForecastType,
    CATEGORY_LABELS_ES,
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MEDIUM,
    DEFAULT_FORECAST_MONTHS,
    FORECAST_LABELS_ES,
    FORECAST_MONTHS_LIST,
    MAX_FORECAST_MONTHS,
    _make_points,
    get_adoption_forecast,
    get_capacity_forecast,
    get_donation_forecast,
    get_intake_forecast,
    get_prediction_summary,
    get_resources_forecast,
    router,
)


# ---------------------------------------------------------------------------
# Enum tests
# ---------------------------------------------------------------------------


class TestEnums:
    """Verify enum members and labels."""

    def test_forecast_type_members(self) -> None:
        assert set(ForecastType) == {
            ForecastType.INTAKE,
            ForecastType.ADOPTIONS,
            ForecastType.DONATIONS,
            ForecastType.CAPACITY,
            ForecastType.RESOURCES,
        }

    def test_confidence_level_members(self) -> None:
        assert set(ConfidenceLevel) == {
            ConfidenceLevel.HIGH,
            ConfidenceLevel.MEDIUM,
            ConfidenceLevel.LOW,
        }

    def test_animal_category_members(self) -> None:
        assert set(AnimalCategory) == {
            AnimalCategory.DOGS,
            AnimalCategory.CATS,
            AnimalCategory.OTHER,
        }

    def test_forecast_labels_cover_all_types(self) -> None:
        for ft in ForecastType:
            assert ft.value in FORECAST_LABELS_ES

    def test_category_labels_cover_all_categories(self) -> None:
        for cat in AnimalCategory:
            assert cat.value in CATEGORY_LABELS_ES


# ---------------------------------------------------------------------------
# Constants tests
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify constant values."""

    def test_default_forecast_months(self) -> None:
        assert DEFAULT_FORECAST_MONTHS == 3

    def test_max_forecast_months(self) -> None:
        assert MAX_FORECAST_MONTHS == 12

    def test_confidence_thresholds_ordered(self) -> None:
        assert CONFIDENCE_HIGH > CONFIDENCE_MEDIUM > CONFIDENCE_LOW

    def test_forecast_months_list_length(self) -> None:
        assert len(FORECAST_MONTHS_LIST) == 12


# ---------------------------------------------------------------------------
# Router config tests
# ---------------------------------------------------------------------------


class TestRouterConfig:
    """Verify router setup."""

    def test_router_prefix(self) -> None:
        assert router.prefix == "/api/admin/analytics/predictions"

    def test_router_tags(self) -> None:
        assert "predictive-analytics" in router.tags


# ---------------------------------------------------------------------------
# Helper tests
# ---------------------------------------------------------------------------


class TestMakePoints:
    """Test _make_points helper."""

    def test_returns_correct_count(self) -> None:
        months = FORECAST_MONTHS_LIST[:3]
        points = _make_points(months=months, base=100.0, growth=0.05, variance=0.1)
        assert len(points) == 3

    def test_returns_all_months(self) -> None:
        points = _make_points(
            months=FORECAST_MONTHS_LIST, base=50.0, growth=0.02, variance=0.15
        )
        assert len(points) == 12

    def test_point_is_forecast_point(self) -> None:
        months = FORECAST_MONTHS_LIST[:1]
        points = _make_points(months=months, base=100.0, growth=0.0, variance=0.1)
        assert isinstance(points[0], ForecastPoint)
        assert points[0].month == months[0]

    def test_bounds_bracket_prediction(self) -> None:
        months = FORECAST_MONTHS_LIST[:3]
        points = _make_points(months=months, base=200.0, growth=0.1, variance=0.2)
        for p in points:
            assert p.lower_bound <= p.predicted <= p.upper_bound

    def test_growth_increases_predicted(self) -> None:
        months = FORECAST_MONTHS_LIST[:3]
        points = _make_points(months=months, base=100.0, growth=0.1, variance=0.1)
        for i in range(1, len(points)):
            assert points[i].predicted > points[i - 1].predicted


# ---------------------------------------------------------------------------
# Endpoint tests
# ---------------------------------------------------------------------------


class TestIntakeForecast:
    """Test GET /intake endpoint."""

    @pytest.mark.asyncio
    async def test_default_months(self) -> None:
        result = await get_intake_forecast(months=DEFAULT_FORECAST_MONTHS)
        assert result.forecast_months == DEFAULT_FORECAST_MONTHS

    @pytest.mark.asyncio
    async def test_has_category_breakdowns(self) -> None:
        result = await get_intake_forecast(months=3)
        assert "dogs" in result.by_category
        assert "cats" in result.by_category
        assert "other" in result.by_category

    @pytest.mark.asyncio
    async def test_total_predicted_positive(self) -> None:
        result = await get_intake_forecast(months=3)
        assert result.total_predicted > 0

    @pytest.mark.asyncio
    async def test_has_factors(self) -> None:
        result = await get_intake_forecast(months=3)
        assert isinstance(result.factors, list)
        assert len(result.factors) > 0

    @pytest.mark.asyncio
    async def test_confidence_level_valid(self) -> None:
        result = await get_intake_forecast(months=3)
        assert result.confidence_level in ConfidenceLevel


class TestAdoptionForecast:
    """Test GET /adoptions endpoint."""

    @pytest.mark.asyncio
    async def test_default_months(self) -> None:
        result = await get_adoption_forecast(months=DEFAULT_FORECAST_MONTHS)
        assert result.forecast_months == DEFAULT_FORECAST_MONTHS

    @pytest.mark.asyncio
    async def test_monthly_points_count(self) -> None:
        result = await get_adoption_forecast(months=6)
        assert len(result.monthly) == 6

    @pytest.mark.asyncio
    async def test_total_predicted_positive(self) -> None:
        result = await get_adoption_forecast(months=3)
        assert result.total_predicted > 0

    @pytest.mark.asyncio
    async def test_bottlenecks_present(self) -> None:
        result = await get_adoption_forecast(months=3)
        assert isinstance(result.bottlenecks, list)

    @pytest.mark.asyncio
    async def test_adoption_rate_trend_present(self) -> None:
        result = await get_adoption_forecast(months=3)
        assert isinstance(result.adoption_rate_trend, str)
        assert len(result.adoption_rate_trend) > 0


class TestDonationForecast:
    """Test GET /donations endpoint."""

    @pytest.mark.asyncio
    async def test_default_months(self) -> None:
        result = await get_donation_forecast(months=DEFAULT_FORECAST_MONTHS)
        assert result.forecast_months == DEFAULT_FORECAST_MONTHS

    @pytest.mark.asyncio
    async def test_dual_currency(self) -> None:
        result = await get_donation_forecast(months=3)
        assert len(result.monthly_pyg) == 3
        assert len(result.monthly_eur) == 3

    @pytest.mark.asyncio
    async def test_totals_positive(self) -> None:
        result = await get_donation_forecast(months=3)
        assert result.total_predicted_pyg > 0
        assert result.total_predicted_eur > 0

    @pytest.mark.asyncio
    async def test_seasonal_factors_present(self) -> None:
        result = await get_donation_forecast(months=3)
        assert isinstance(result.seasonal_factors, list)


class TestCapacityForecast:
    """Test GET /capacity endpoint."""

    @pytest.mark.asyncio
    async def test_default_months(self) -> None:
        result = await get_capacity_forecast(months=DEFAULT_FORECAST_MONTHS)
        assert result.forecast_months == DEFAULT_FORECAST_MONTHS

    @pytest.mark.asyncio
    async def test_monthly_points_count(self) -> None:
        result = await get_capacity_forecast(months=6)
        assert len(result.monthly) == 6

    @pytest.mark.asyncio
    async def test_current_occupancy_present(self) -> None:
        result = await get_capacity_forecast(months=3)
        assert result.current_occupancy_pct > 0

    @pytest.mark.asyncio
    async def test_recommendations_present(self) -> None:
        result = await get_capacity_forecast(months=3)
        assert isinstance(result.recommendations, list)
        assert len(result.recommendations) > 0

    @pytest.mark.asyncio
    async def test_peak_month_present(self) -> None:
        result = await get_capacity_forecast(months=3)
        assert isinstance(result.peak_month, str)
        assert len(result.peak_month) > 0


class TestResourceForecast:
    """Test GET /resources endpoint."""

    @pytest.mark.asyncio
    async def test_default_months(self) -> None:
        result = await get_resources_forecast(months=DEFAULT_FORECAST_MONTHS)
        assert result.forecast_months == DEFAULT_FORECAST_MONTHS

    @pytest.mark.asyncio
    async def test_all_resource_types(self) -> None:
        result = await get_resources_forecast(months=3)
        assert len(result.food_kg) == 3
        assert len(result.medical_supplies) == 3
        assert len(result.volunteer_hours) == 3

    @pytest.mark.asyncio
    async def test_budget_positive(self) -> None:
        result = await get_resources_forecast(months=3)
        assert result.budget_needed_pyg > 0


class TestPredictionSummary:
    """Test GET /summary endpoint."""

    @pytest.mark.asyncio
    async def test_default_months(self) -> None:
        result = await get_prediction_summary(months=DEFAULT_FORECAST_MONTHS)
        assert result.forecast_months == DEFAULT_FORECAST_MONTHS

    @pytest.mark.asyncio
    async def test_has_highlights(self) -> None:
        result = await get_prediction_summary(months=3)
        assert isinstance(result.highlights, list)
        assert len(result.highlights) > 0

    @pytest.mark.asyncio
    async def test_has_risks(self) -> None:
        result = await get_prediction_summary(months=3)
        assert isinstance(result.risks, list)
        assert len(result.risks) > 0

    @pytest.mark.asyncio
    async def test_has_opportunities(self) -> None:
        result = await get_prediction_summary(months=3)
        assert isinstance(result.opportunities, list)
        assert len(result.opportunities) > 0

    @pytest.mark.asyncio
    async def test_generated_at_present(self) -> None:
        result = await get_prediction_summary(months=3)
        assert result.generated_at is not None
        assert len(result.generated_at) > 0


# ---------------------------------------------------------------------------
# Frontend file assertions
# ---------------------------------------------------------------------------


class TestFrontendFile:
    """Verify frontend page exists."""

    def test_page_file_exists(self) -> None:
        from pathlib import Path

        page = Path("frontend/src/app/admin/analytics/predicciones/page.tsx")
        assert page.exists(), "Frontend page must exist"
        content = page.read_text()
        assert "PrediccionesPage" in content
        assert "Analisis predictivo" in content
