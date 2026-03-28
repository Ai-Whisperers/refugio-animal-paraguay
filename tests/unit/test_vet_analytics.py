"""Tests for veterinary care analytics feature (RAP-636).

Covers:
    - Module structure and constants
    - API endpoints and response schemas
    - Sample data integrity
    - Frontend page structure and accessibility
"""

from pathlib import Path

import pytest


class TestModuleStructure:
    def test_module_imports(self) -> None:
        from src.api import vet_analytics

        assert hasattr(vet_analytics, "router")

    def test_router_has_prefix(self) -> None:
        from src.api.vet_analytics import router

        assert any(
            r.path.startswith("/api/admin/analytics/veterinary")
            for r in router.routes
            if hasattr(r, "path")
        )

    def test_router_has_tag(self) -> None:
        from src.api.vet_analytics import router

        assert "vet-analytics" in router.tags

    def test_treatment_category_enum(self) -> None:
        from src.api.vet_analytics import TreatmentCategory

        assert hasattr(TreatmentCategory, "VACCINATION")
        assert hasattr(TreatmentCategory, "STERILIZATION")
        assert hasattr(TreatmentCategory, "SURGERY")

    def test_species_type_enum(self) -> None:
        from src.api.vet_analytics import SpeciesType

        assert hasattr(SpeciesType, "DOG")
        assert hasattr(SpeciesType, "CAT")


class TestConstants:
    def test_default_period_days(self) -> None:
        from src.api.vet_analytics import DEFAULT_PERIOD_DAYS

        assert DEFAULT_PERIOD_DAYS == 30

    def test_max_period_days(self) -> None:
        from src.api.vet_analytics import MAX_PERIOD_DAYS

        assert MAX_PERIOD_DAYS == 365

    def test_currency(self) -> None:
        from src.api.vet_analytics import CURRENCY_PYG

        assert CURRENCY_PYG == "PYG"

    def test_treatment_labels_spanish(self) -> None:
        from src.api.vet_analytics import TREATMENT_LABELS_ES

        assert "vaccination" in TREATMENT_LABELS_ES
        assert len(TREATMENT_LABELS_ES) == 8


class TestSampleData:
    def test_sample_treatments_exist(self) -> None:
        from src.api.vet_analytics import SAMPLE_TREATMENTS

        assert len(SAMPLE_TREATMENTS) == 8

    def test_sample_treatments_percentages_sum(self) -> None:
        from src.api.vet_analytics import SAMPLE_TREATMENTS

        total = sum(t.percentage for t in SAMPLE_TREATMENTS)
        assert 99.0 <= total <= 101.0

    def test_sample_species_exist(self) -> None:
        from src.api.vet_analytics import SAMPLE_SPECIES

        assert len(SAMPLE_SPECIES) == 3

    def test_sample_monthly_exist(self) -> None:
        from src.api.vet_analytics import SAMPLE_MONTHLY

        assert len(SAMPLE_MONTHLY) == 6

    def test_sample_costs_exist(self) -> None:
        from src.api.vet_analytics import SAMPLE_COSTS

        assert len(SAMPLE_COSTS) >= 5


class TestAPIEndpoints:
    @pytest.mark.asyncio
    async def test_get_vet_summary(self) -> None:
        from src.api.vet_analytics import get_vet_summary

        result = await get_vet_summary(period_days=30)
        assert result.total_treatments > 0
        assert result.total_vaccinations > 0
        assert result.total_sterilizations > 0
        assert result.total_animals_treated > 0

    @pytest.mark.asyncio
    async def test_get_treatment_breakdown(self) -> None:
        from src.api.vet_analytics import get_treatment_breakdown

        result = await get_treatment_breakdown(period_days=30)
        assert len(result.treatments) == 8
        assert result.total > 0

    @pytest.mark.asyncio
    async def test_get_vaccination_stats(self) -> None:
        from src.api.vet_analytics import get_vaccination_stats

        result = await get_vaccination_stats(period_days=30)
        assert result.vaccination_rate > 0
        assert result.most_common_vaccine != ""

    @pytest.mark.asyncio
    async def test_get_sterilization_stats(self) -> None:
        from src.api.vet_analytics import get_sterilization_stats

        result = await get_sterilization_stats(period_days=30)
        assert result.sterilization_rate > 0
        assert result.dogs_sterilized + result.cats_sterilized == result.total_sterilized

    @pytest.mark.asyncio
    async def test_get_cost_analysis(self) -> None:
        from src.api.vet_analytics import get_cost_analysis

        result = await get_cost_analysis(period_days=30)
        assert result.total_cost > 0
        assert len(result.by_category) >= 5
        assert result.currency == "PYG"

    @pytest.mark.asyncio
    async def test_get_vet_trends(self) -> None:
        from src.api.vet_analytics import get_vet_trends

        result = await get_vet_trends(months=6)
        assert len(result.monthly) <= 6
        assert result.period_months == 6

    @pytest.mark.asyncio
    async def test_get_vet_trends_limited(self) -> None:
        from src.api.vet_analytics import get_vet_trends

        result = await get_vet_trends(months=3)
        assert len(result.monthly) <= 3

    @pytest.mark.asyncio
    async def test_summary_with_custom_period(self) -> None:
        from src.api.vet_analytics import get_vet_summary

        result = await get_vet_summary(period_days=90)
        assert result.period_days == 90


class TestSchemas:
    def test_vet_summary_schema(self) -> None:
        from src.api.vet_analytics import VetSummary

        s = VetSummary(
            total_treatments=10,
            total_vaccinations=5,
            total_sterilizations=3,
            total_animals_treated=8,
            avg_treatments_per_animal=1.25,
            period_days=30,
            generated_at="2026-01-01",
        )
        assert s.total_treatments == 10

    def test_treatment_count_schema(self) -> None:
        from src.api.vet_analytics import TreatmentCategory, TreatmentCount

        t = TreatmentCount(
            category=TreatmentCategory.VACCINATION,
            category_label="Vacunación",
            count=10,
            percentage=50.0,
        )
        assert t.count == 10

    def test_cost_item_schema(self) -> None:
        from src.api.vet_analytics import CostItem

        c = CostItem(
            category="vaccination",
            category_label="Vacunación",
            total_cost=100000,
            avg_cost_per_treatment=10000,
            count=10,
        )
        assert c.currency == "PYG"


class TestVetAnalyticsPage:
    @pytest.fixture
    def page_content(self) -> str:
        page_path = Path("frontend/src/app/admin/analytics/veterinaria/page.tsx")
        assert page_path.exists()
        return page_path.read_text()

    def test_is_client_component(self, page_content: str) -> None:
        assert '"use client"' in page_content

    def test_has_metric_cards(self, page_content: str) -> None:
        assert "MetricCard" in page_content

    def test_has_horizontal_bars(self, page_content: str) -> None:
        assert "HorizontalBar" in page_content

    def test_has_trend_chart(self, page_content: str) -> None:
        assert "TrendChart" in page_content

    def test_has_cost_table(self, page_content: str) -> None:
        assert "CostTable" in page_content

    def test_has_period_selector(self, page_content: str) -> None:
        assert "PERIOD_OPTIONS" in page_content
        assert "periodDays" in page_content

    def test_has_vaccination_section(self, page_content: str) -> None:
        assert "Vacunaciones" in page_content
        assert "vaccination_rate" in page_content

    def test_has_sterilization_section(self, page_content: str) -> None:
        assert "Esterilizaciones" in page_content
        assert "sterilization_rate" in page_content

    def test_has_cost_section(self, page_content: str) -> None:
        assert "costos" in page_content.lower()

    def test_has_loading_skeleton(self, page_content: str) -> None:
        assert "LoadingSkeleton" in page_content

    def test_has_spanish_content(self, page_content: str) -> None:
        assert "veterinaria" in page_content.lower()
        assert "tratamientos" in page_content.lower()

    def test_fetches_all_endpoints(self, page_content: str) -> None:
        assert "/summary" in page_content
        assert "/treatments" in page_content
        assert "/vaccinations" in page_content
        assert "/sterilizations" in page_content
        assert "/costs" in page_content
        assert "/trends" in page_content


class TestAccessibility:
    @pytest.fixture
    def page_content(self) -> str:
        page_path = Path("frontend/src/app/admin/analytics/veterinaria/page.tsx")
        return page_path.read_text()

    def test_has_aria_labels(self, page_content: str) -> None:
        assert "aria-label" in page_content

    def test_has_aria_busy(self, page_content: str) -> None:
        assert "aria-busy" in page_content

    def test_has_role_alert(self, page_content: str) -> None:
        assert 'role="alert"' in page_content

    def test_has_role_img(self, page_content: str) -> None:
        assert 'role="img"' in page_content

    def test_has_role_list(self, page_content: str) -> None:
        assert 'role="list"' in page_content

    def test_has_aria_hidden(self, page_content: str) -> None:
        assert 'aria-hidden="true"' in page_content

    def test_has_table_aria(self, page_content: str) -> None:
        assert "aria-label" in page_content

    def test_has_min_touch_targets(self, page_content: str) -> None:
        assert "min-h-[44px]" in page_content


class TestAppRegistration:
    def test_router_imported(self) -> None:
        content = Path("src/app.py").read_text()
        assert "vet_analytics_router" in content
