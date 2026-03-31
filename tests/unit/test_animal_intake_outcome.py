"""Tests for animal intake and outcome analytics API."""

import pytest
from src.api.animal_intake_outcome import (
    DEFAULT_PERIOD_DAYS,
    INTAKE_LABELS_ES,
    MAX_PERIOD_DAYS,
    MONTHLY_DATA,
    MONTHS_FOR_TREND,
    OUTCOME_LABELS_ES,
    SPECIES_LABELS_ES,
    IntakeSource,
    OutcomeType,
    Species,
    get_demographics,
    get_intake_breakdown,
    get_length_of_stay,
    get_outcome_breakdown,
    get_overview,
    get_trends,
    router,
)

# ---------------------------------------------------------------------------
# Enum tests
# ---------------------------------------------------------------------------


class TestEnums:
    """Verify enum members and labels."""

    def test_intake_source_members(self) -> None:
        assert len(IntakeSource) == 6

    def test_outcome_type_members(self) -> None:
        assert len(OutcomeType) == 6

    def test_species_members(self) -> None:
        assert set(Species) == {Species.DOG, Species.CAT, Species.OTHER}

    def test_intake_labels_cover_all(self) -> None:
        for s in IntakeSource:
            assert s.value in INTAKE_LABELS_ES

    def test_outcome_labels_cover_all(self) -> None:
        for o in OutcomeType:
            assert o.value in OUTCOME_LABELS_ES

    def test_species_labels_cover_all(self) -> None:
        for sp in Species:
            assert sp.value in SPECIES_LABELS_ES


# ---------------------------------------------------------------------------
# Constants tests
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify constant values."""

    def test_default_period(self) -> None:
        assert DEFAULT_PERIOD_DAYS == 30

    def test_max_period(self) -> None:
        assert MAX_PERIOD_DAYS == 365

    def test_months_for_trend(self) -> None:
        assert MONTHS_FOR_TREND == 12

    def test_monthly_data_length(self) -> None:
        assert len(MONTHLY_DATA) == 12

    def test_monthly_data_has_required_keys(self) -> None:
        for m in MONTHLY_DATA:
            assert "month" in m
            assert "intake" in m
            assert "outcomes" in m
            assert "population" in m
            assert "adoptions" in m


# ---------------------------------------------------------------------------
# Router config tests
# ---------------------------------------------------------------------------


class TestRouterConfig:
    """Verify router setup."""

    def test_router_prefix(self) -> None:
        assert router.prefix == "/api/admin/analytics/animals"

    def test_router_tags(self) -> None:
        assert "animal-analytics" in router.tags


# ---------------------------------------------------------------------------
# Endpoint tests
# ---------------------------------------------------------------------------


class TestOverview:
    """Test GET /overview endpoint."""

    @pytest.mark.asyncio
    async def test_default_period(self) -> None:
        result = await get_overview(period_days=DEFAULT_PERIOD_DAYS)
        assert result.period_days == DEFAULT_PERIOD_DAYS

    @pytest.mark.asyncio
    async def test_current_population_positive(self) -> None:
        result = await get_overview(period_days=30)
        assert result.current_population > 0

    @pytest.mark.asyncio
    async def test_intake_and_outcomes_positive(self) -> None:
        result = await get_overview(period_days=30)
        assert result.total_intake > 0
        assert result.total_outcomes > 0

    @pytest.mark.asyncio
    async def test_rates_positive(self) -> None:
        result = await get_overview(period_days=30)
        assert result.intake_rate_per_day > 0
        assert result.outcome_rate_per_day > 0

    @pytest.mark.asyncio
    async def test_live_release_rate_valid(self) -> None:
        result = await get_overview(period_days=30)
        assert 0 <= result.live_release_rate_pct <= 100

    @pytest.mark.asyncio
    async def test_generated_at_present(self) -> None:
        result = await get_overview(period_days=30)
        assert result.generated_at is not None


class TestIntakeBreakdown:
    """Test GET /intake endpoint."""

    @pytest.mark.asyncio
    async def test_total_positive(self) -> None:
        result = await get_intake_breakdown(period_days=30)
        assert result.total > 0

    @pytest.mark.asyncio
    async def test_has_sources(self) -> None:
        result = await get_intake_breakdown(period_days=30)
        assert len(result.by_source) > 0

    @pytest.mark.asyncio
    async def test_has_species(self) -> None:
        result = await get_intake_breakdown(period_days=30)
        assert len(result.by_species) > 0

    @pytest.mark.asyncio
    async def test_has_monthly_trend(self) -> None:
        result = await get_intake_breakdown(period_days=30)
        assert len(result.monthly_trend) > 0


class TestOutcomeBreakdown:
    """Test GET /outcomes endpoint."""

    @pytest.mark.asyncio
    async def test_total_positive(self) -> None:
        result = await get_outcome_breakdown(period_days=30)
        assert result.total > 0

    @pytest.mark.asyncio
    async def test_has_types(self) -> None:
        result = await get_outcome_breakdown(period_days=30)
        assert len(result.by_type) > 0

    @pytest.mark.asyncio
    async def test_live_release_rate_valid(self) -> None:
        result = await get_outcome_breakdown(period_days=30)
        assert 0 <= result.live_release_rate_pct <= 100

    @pytest.mark.asyncio
    async def test_has_species(self) -> None:
        result = await get_outcome_breakdown(period_days=30)
        assert len(result.by_species) > 0


class TestDemographics:
    """Test GET /demographics endpoint."""

    @pytest.mark.asyncio
    async def test_population_positive(self) -> None:
        result = await get_demographics()
        assert result.total_population > 0

    @pytest.mark.asyncio
    async def test_has_species(self) -> None:
        result = await get_demographics()
        assert len(result.by_species) > 0

    @pytest.mark.asyncio
    async def test_has_age_groups(self) -> None:
        result = await get_demographics()
        assert len(result.by_age_group) > 0

    @pytest.mark.asyncio
    async def test_has_sex_breakdown(self) -> None:
        result = await get_demographics()
        assert len(result.by_sex) == 2

    @pytest.mark.asyncio
    async def test_sterilization_rate_valid(self) -> None:
        result = await get_demographics()
        assert 0 <= result.sterilization_rate_pct <= 100


class TestLengthOfStay:
    """Test GET /length-of-stay endpoint."""

    @pytest.mark.asyncio
    async def test_average_positive(self) -> None:
        result = await get_length_of_stay()
        assert result.average_days > 0

    @pytest.mark.asyncio
    async def test_median_positive(self) -> None:
        result = await get_length_of_stay()
        assert result.median_days > 0

    @pytest.mark.asyncio
    async def test_min_less_than_max(self) -> None:
        result = await get_length_of_stay()
        assert result.min_days < result.max_days

    @pytest.mark.asyncio
    async def test_has_species_breakdown(self) -> None:
        result = await get_length_of_stay()
        assert len(result.by_species) > 0

    @pytest.mark.asyncio
    async def test_has_distribution(self) -> None:
        result = await get_length_of_stay()
        assert len(result.distribution) > 0

    @pytest.mark.asyncio
    async def test_has_outcome_breakdown(self) -> None:
        result = await get_length_of_stay()
        assert len(result.by_outcome) > 0


class TestTrends:
    """Test GET /trends endpoint."""

    @pytest.mark.asyncio
    async def test_default_months(self) -> None:
        result = await get_trends(months=MONTHS_FOR_TREND)
        assert result.months == MONTHS_FOR_TREND

    @pytest.mark.asyncio
    async def test_custom_months(self) -> None:
        result = await get_trends(months=6)
        assert result.months == 6

    @pytest.mark.asyncio
    async def test_data_present(self) -> None:
        result = await get_trends(months=12)
        assert len(result.data) == 12

    @pytest.mark.asyncio
    async def test_trends_valid_values(self) -> None:
        result = await get_trends(months=12)
        valid_trends = {"increasing", "decreasing", "stable"}
        assert result.intake_trend in valid_trends
        assert result.outcome_trend in valid_trends
        assert result.population_trend in valid_trends


# ---------------------------------------------------------------------------
# Frontend file assertions
# ---------------------------------------------------------------------------


class TestFrontendFile:
    """Verify frontend page exists."""

    def test_page_file_exists(self) -> None:
        from pathlib import Path

        page = Path("frontend/src/app/admin/analytics/animales/page.tsx")
        assert page.exists(), "Frontend page must exist"
        content = page.read_text()
        assert "AnimalAnalyticsPage" in content
        assert "Analytics de animales" in content
