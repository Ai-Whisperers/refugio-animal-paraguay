"""Tests for RAP-608: Donor impact summaries.

Covers impact calculations, statement generation, comparison logic, and API.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SERVICE_FILE = PROJECT_ROOT / "src" / "services" / "donor_impact.py"
API_FILE = PROJECT_ROOT / "src" / "api" / "donor_impact.py"
APP_FILE = PROJECT_ROOT / "src" / "app.py"


# ---------------------------------------------------------------------------
# Module structure
# ---------------------------------------------------------------------------


class TestModuleStructure:
    """Verify module files and registration."""

    def test_service_file_exists(self) -> None:
        assert SERVICE_FILE.exists()

    def test_api_file_exists(self) -> None:
        assert API_FILE.exists()

    def test_registered_in_app(self) -> None:
        content = APP_FILE.read_text()
        assert "donor_impact_router" in content

    def test_router_prefix(self) -> None:
        from src.api.donor_impact import router

        assert router.prefix == "/api/portal"

    def test_router_tags(self) -> None:
        from src.api.donor_impact import router

        assert "donor-impact" in router.tags


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify service constants."""

    def test_cache_ttl(self) -> None:
        from src.services.donor_impact import CACHE_TTL_SECONDS

        assert CACHE_TTL_SECONDS == 86_400

    def test_pyg_to_usd_rate(self) -> None:
        from src.services.donor_impact import PYG_TO_USD_RATE

        assert 0 < PYG_TO_USD_RATE < 1

    def test_default_allocation_sums_to_one(self) -> None:
        from src.services.donor_impact import DEFAULT_ALLOCATION

        total = sum(DEFAULT_ALLOCATION.values())
        assert abs(total - 1.0) < 0.01

    def test_default_allocation_has_seven_categories(self) -> None:
        from src.services.donor_impact import DEFAULT_ALLOCATION

        assert len(DEFAULT_ALLOCATION) == 7

    def test_category_labels_spanish(self) -> None:
        from src.services.donor_impact import CATEGORY_LABELS_ES

        assert CATEGORY_LABELS_ES["medical"] == "Medico"
        assert CATEGORY_LABELS_ES["food"] == "Comida"
        assert CATEGORY_LABELS_ES["rescue"] == "Rescate"

    def test_cost_constants_positive(self) -> None:
        from src.services.donor_impact import (
            AVERAGE_CASTRATION_COST_PYG,
            AVERAGE_DAILY_FOOD_COST_PYG,
            AVERAGE_MEDICAL_TREATMENT_COST_PYG,
            AVERAGE_RESCUE_COST_PYG,
        )

        assert AVERAGE_RESCUE_COST_PYG > 0
        assert AVERAGE_CASTRATION_COST_PYG > 0
        assert AVERAGE_MEDICAL_TREATMENT_COST_PYG > 0
        assert AVERAGE_DAILY_FOOD_COST_PYG > 0


# ---------------------------------------------------------------------------
# Impact calculations
# ---------------------------------------------------------------------------


class TestCalculateImpactMetrics:
    """Test impact metric calculations."""

    def test_zero_donations(self) -> None:
        from src.services.donor_impact import calculate_impact_metrics

        metrics = calculate_impact_metrics(0)
        assert metrics.animals_rescued == 0
        assert metrics.castrations_funded == 0
        assert metrics.animals_treated == 0
        assert metrics.animals_fed_estimate_days == 0

    def test_positive_donations(self) -> None:
        from src.services.donor_impact import calculate_impact_metrics

        metrics = calculate_impact_metrics(10_000_000)
        assert metrics.animals_rescued > 0
        assert metrics.animals_treated > 0
        assert metrics.animals_fed_estimate_days > 0

    def test_custom_allocation(self) -> None:
        from src.services.donor_impact import calculate_impact_metrics

        alloc = {"rescue": 1.0, "medical": 0.0, "food": 0.0}
        metrics = calculate_impact_metrics(10_000_000, allocation=alloc)
        assert metrics.animals_rescued > 0
        assert metrics.animals_treated == 0
        assert metrics.animals_fed_estimate_days == 0

    def test_food_only_allocation(self) -> None:
        from src.services.donor_impact import calculate_impact_metrics

        alloc = {"rescue": 0.0, "medical": 0.0, "food": 1.0}
        metrics = calculate_impact_metrics(10_000_000, allocation=alloc)
        assert metrics.animals_rescued == 0
        assert metrics.animals_fed_estimate_days > 0

    def test_emergency_cases_minimum_one(self) -> None:
        from src.services.donor_impact import calculate_impact_metrics

        metrics = calculate_impact_metrics(10_000_000)
        assert metrics.emergency_cases_funded >= 1

    def test_metrics_scale_with_amount(self) -> None:
        from src.services.donor_impact import calculate_impact_metrics

        small = calculate_impact_metrics(1_000_000)
        large = calculate_impact_metrics(100_000_000)
        assert large.animals_rescued >= small.animals_rescued
        assert large.animals_fed_estimate_days >= small.animals_fed_estimate_days


# ---------------------------------------------------------------------------
# Impact statements
# ---------------------------------------------------------------------------


class TestGenerateImpactStatements:
    """Test personalized impact statement generation."""

    def test_statements_with_donations(self) -> None:
        from src.services.donor_impact import (
            ImpactMetrics,
            generate_impact_statements,
        )

        impact = ImpactMetrics(
            animals_rescued=5,
            emergency_cases_funded=2,
            castrations_funded=3,
            animals_treated=10,
            animals_fed_estimate_days=30,
        )
        statements = generate_impact_statements("Maria", impact)
        assert len(statements) > 0
        assert any("Maria" in s for s in statements)

    def test_statements_mention_rescue(self) -> None:
        from src.services.donor_impact import (
            ImpactMetrics,
            generate_impact_statements,
        )

        impact = ImpactMetrics(animals_rescued=5)
        statements = generate_impact_statements("Juan", impact)
        assert any("rescatar" in s for s in statements)

    def test_statements_in_spanish(self) -> None:
        from src.services.donor_impact import (
            ImpactMetrics,
            generate_impact_statements,
        )

        impact = ImpactMetrics(
            animals_rescued=1,
            castrations_funded=1,
            animals_treated=1,
            animals_fed_estimate_days=10,
        )
        statements = generate_impact_statements("Ana", impact)
        assert any("donaciones" in s for s in statements)

    def test_fallback_statement_for_zero_impact(self) -> None:
        from src.services.donor_impact import (
            ImpactMetrics,
            generate_impact_statements,
        )

        impact = ImpactMetrics()
        statements = generate_impact_statements("Carlos", impact)
        assert len(statements) == 1
        assert "Carlos" in statements[0]
        assert "apoyo" in statements[0]

    def test_castration_statement(self) -> None:
        from src.services.donor_impact import (
            ImpactMetrics,
            generate_impact_statements,
        )

        impact = ImpactMetrics(castrations_funded=5)
        statements = generate_impact_statements("Eva", impact)
        assert any("castrar" in s for s in statements)

    def test_food_statement(self) -> None:
        from src.services.donor_impact import (
            ImpactMetrics,
            generate_impact_statements,
        )

        impact = ImpactMetrics(animals_fed_estimate_days=100)
        statements = generate_impact_statements("Luis", impact)
        assert any("alimento" in s for s in statements)


# ---------------------------------------------------------------------------
# Donor comparison
# ---------------------------------------------------------------------------


class TestDonorComparison:
    """Test donor ranking and comparison."""

    def test_rank_with_no_other_donors(self) -> None:
        from src.services.donor_impact import calculate_donor_comparison

        comp = calculate_donor_comparison(500_000, [])
        assert comp.rank_this_year == 1
        assert "comunidad" in comp.comparison_text

    def test_rank_with_other_donors(self) -> None:
        from src.services.donor_impact import calculate_donor_comparison

        totals = [1_000_000, 800_000, 600_000, 400_000, 200_000]
        comp = calculate_donor_comparison(700_000, totals)
        assert comp.rank_this_year > 0
        assert comp.total_donors_this_year == 5
        assert "#" in comp.comparison_text

    def test_top_donor(self) -> None:
        from src.services.donor_impact import calculate_donor_comparison

        totals = [500_000, 300_000]
        comp = calculate_donor_comparison(1_000_000, totals)
        assert comp.rank_this_year == 1

    def test_castration_goal_percentage(self) -> None:
        from src.services.donor_impact import calculate_donor_comparison

        comp = calculate_donor_comparison(5_000_000, castration_goal_pyg=10_000_000)
        assert comp.castration_goal_percentage == 50.0

    def test_castration_goal_capped_at_100(self) -> None:
        from src.services.donor_impact import calculate_donor_comparison

        comp = calculate_donor_comparison(20_000_000, castration_goal_pyg=10_000_000)
        assert comp.castration_goal_percentage == 100.0


# ---------------------------------------------------------------------------
# Full summary generation
# ---------------------------------------------------------------------------


class TestGenerateDonorImpactSummary:
    """Test complete summary generation."""

    def test_basic_summary(self) -> None:
        from src.services.donor_impact import generate_donor_impact_summary

        summary = generate_donor_impact_summary(
            donor_id="d-1",
            donor_name="Maria",
            total_donated_pyg=5_000_000,
        )
        assert summary.donor_id == "d-1"
        assert summary.donor_name == "Maria"
        assert summary.total_donated_pyg == 5_000_000
        assert summary.total_donated_usd > 0
        assert summary.currency == "PYG"

    def test_summary_has_allocation(self) -> None:
        from src.services.donor_impact import generate_donor_impact_summary

        summary = generate_donor_impact_summary(
            donor_id="d-2",
            total_donated_pyg=1_000_000,
        )
        assert len(summary.allocation) == 7
        assert "medical" in summary.allocation

    def test_summary_has_labels(self) -> None:
        from src.services.donor_impact import generate_donor_impact_summary

        summary = generate_donor_impact_summary(
            donor_id="d-3",
            total_donated_pyg=1_000_000,
        )
        assert "medical" in summary.allocation_labels
        assert summary.allocation_labels["medical"] == "Medico"

    def test_summary_has_impact_statements(self) -> None:
        from src.services.donor_impact import generate_donor_impact_summary

        summary = generate_donor_impact_summary(
            donor_id="d-4",
            donor_name="Juan",
            total_donated_pyg=10_000_000,
        )
        assert len(summary.impact_statements) > 0

    def test_zero_donation_summary(self) -> None:
        from src.services.donor_impact import generate_donor_impact_summary

        summary = generate_donor_impact_summary(
            donor_id="d-5",
            donor_name="Pedro",
            total_donated_pyg=0,
        )
        assert summary.total_donated_pyg == 0
        assert len(summary.impact_statements) > 0

    def test_summary_to_dict(self) -> None:
        from src.services.donor_impact import (
            generate_donor_impact_summary,
            impact_summary_to_dict,
        )

        summary = generate_donor_impact_summary(
            donor_id="d-6",
            total_donated_pyg=5_000_000,
        )
        d = impact_summary_to_dict(summary)
        assert "donor_id" in d
        assert "impact" in d
        assert "animals_rescued" in d["impact"]
        assert "comparison" in d
        assert "cache_ttl_seconds" in d


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


class TestDonorImpactAPI:
    """Test API endpoints."""

    @pytest.fixture()
    def client(self) -> TestClient:
        from src.app import app

        return TestClient(app)

    def test_get_impact_default(self, client: TestClient) -> None:
        response = client.get("/api/portal/impact")
        assert response.status_code == 200
        data = response.json()
        assert "donor_id" in data
        assert "impact" in data

    def test_get_impact_with_donations(self, client: TestClient) -> None:
        response = client.get("/api/portal/impact?donor_name=Maria&total_donated_pyg=5000000")
        assert response.status_code == 200
        data = response.json()
        assert data["donor_name"] == "Maria"
        assert data["total_donated_pyg"] == 5_000_000

    def test_get_impact_has_allocation(self, client: TestClient) -> None:
        response = client.get("/api/portal/impact?total_donated_pyg=1000000")
        data = response.json()
        assert "allocation" in data
        assert "medical" in data["allocation"]

    def test_get_impact_has_statements(self, client: TestClient) -> None:
        response = client.get("/api/portal/impact?total_donated_pyg=10000000&donor_name=Juan")
        data = response.json()
        assert len(data["impact_statements"]) > 0

    def test_get_impact_has_campaigns(self, client: TestClient) -> None:
        response = client.get("/api/portal/impact?total_donated_pyg=5000000")
        data = response.json()
        assert len(data["top_campaigns"]) > 0

    def test_get_impact_zero_donations(self, client: TestClient) -> None:
        response = client.get("/api/portal/impact?total_donated_pyg=0")
        data = response.json()
        assert data["total_donated_pyg"] == 0
        assert data["impact"]["animals_rescued"] == 0

    def test_get_statements_only(self, client: TestClient) -> None:
        response = client.get(
            "/api/portal/impact/statements?donor_name=Ana&total_donated_pyg=5000000"
        )
        assert response.status_code == 200
        statements = response.json()
        assert isinstance(statements, list)
        assert len(statements) > 0

    def test_get_statements_zero_donations(self, client: TestClient) -> None:
        response = client.get("/api/portal/impact/statements?donor_name=Carlos&total_donated_pyg=0")
        assert response.status_code == 200
        statements = response.json()
        assert len(statements) > 0
