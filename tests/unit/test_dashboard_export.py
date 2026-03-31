"""Unit tests for the operational dashboard export endpoints (RAP-254)."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from src.api.operational_dashboard import router
from src.auth.dependencies import require_staff
from src.db.session import get_db
from src.services.operational_metrics_service import (
    OccupancyMetrics,
    OperationalMetrics,
    PeriodCounts,
    PopulationBreakdown,
    SpeciesBreakdown,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_metrics(
    current_count: int = 80,
    capacity: int = 200,
    intake_count: int = 15,
    outcome_count: int = 10,
    period_days: int = 30,
    avg_los_days: float = 20.5,
) -> OperationalMetrics:
    """Build a fully-populated OperationalMetrics fixture."""
    population = PopulationBreakdown(
        intake=5,
        quarantine=10,
        available=40,
        foster=8,
        under_treatment=7,
        adopted=120,
        deceased=3,
    )
    occupancy = OccupancyMetrics(current_count=current_count, capacity=capacity)
    period = PeriodCounts(
        period_days=period_days,
        intake_count=intake_count,
        outcome_count=outcome_count,
    )
    species = SpeciesBreakdown(dog=50, cat=25, other=5)
    return OperationalMetrics(
        generated_at="2026-03-29T10:00:00+00:00",
        population=population,
        occupancy=occupancy,
        period=period,
        species=species,
        avg_los_days=avg_los_days,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def app() -> FastAPI:
    """FastAPI app with the operational dashboard router."""
    test_app = FastAPI()
    test_app.include_router(router)
    return test_app


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client with auth and DB dependencies overridden."""
    from src.db.models.user import User

    mock_user = MagicMock(spec=User)
    mock_user.role = "staff"

    app.dependency_overrides[require_staff] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: AsyncMock()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# /export/metrics tests
# ---------------------------------------------------------------------------


class TestExportMetricsCsv:
    @pytest.mark.asyncio
    async def test_returns_200_with_csv_content_type(self, client: AsyncClient) -> None:
        with patch(
            "src.api.operational_dashboard.get_operational_metrics",
            new=AsyncMock(return_value=_make_metrics()),
        ):
            response = await client.get("/api/admin/operational-dashboard/export/metrics")
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_content_disposition_header(self, client: AsyncClient) -> None:
        with patch(
            "src.api.operational_dashboard.get_operational_metrics",
            new=AsyncMock(return_value=_make_metrics()),
        ):
            response = await client.get("/api/admin/operational-dashboard/export/metrics")
        assert "dashboard-metrics.csv" in response.headers.get("content-disposition", "")

    @pytest.mark.asyncio
    async def test_csv_has_header_row(self, client: AsyncClient) -> None:
        with patch(
            "src.api.operational_dashboard.get_operational_metrics",
            new=AsyncMock(return_value=_make_metrics()),
        ):
            response = await client.get("/api/admin/operational-dashboard/export/metrics")
        lines = response.text.strip().split("\n")
        assert len(lines) >= 1
        header = lines[0]
        assert "generated_at" in header
        assert "occupancy_rate_pct" in header

    @pytest.mark.asyncio
    async def test_csv_has_data_row(self, client: AsyncClient) -> None:
        with patch(
            "src.api.operational_dashboard.get_operational_metrics",
            new=AsyncMock(return_value=_make_metrics()),
        ):
            response = await client.get("/api/admin/operational-dashboard/export/metrics")
        lines = response.text.strip().split("\n")
        # One header row + one data row
        assert len(lines) == 2

    @pytest.mark.asyncio
    async def test_csv_contains_occupancy_rate(self, client: AsyncClient) -> None:
        metrics = _make_metrics(current_count=100, capacity=200)  # 50%
        with patch(
            "src.api.operational_dashboard.get_operational_metrics",
            new=AsyncMock(return_value=metrics),
        ):
            response = await client.get("/api/admin/operational-dashboard/export/metrics")
        assert "50.0" in response.text

    @pytest.mark.asyncio
    async def test_csv_contains_avg_los(self, client: AsyncClient) -> None:
        metrics = _make_metrics(avg_los_days=20.5)
        with patch(
            "src.api.operational_dashboard.get_operational_metrics",
            new=AsyncMock(return_value=metrics),
        ):
            response = await client.get("/api/admin/operational-dashboard/export/metrics")
        assert "20.5" in response.text

    @pytest.mark.asyncio
    async def test_csv_contains_species_counts(self, client: AsyncClient) -> None:
        metrics = _make_metrics()
        with patch(
            "src.api.operational_dashboard.get_operational_metrics",
            new=AsyncMock(return_value=metrics),
        ):
            response = await client.get("/api/admin/operational-dashboard/export/metrics")
        # dog=50, cat=25, other=5
        assert "50" in response.text
        assert "25" in response.text

    @pytest.mark.asyncio
    async def test_csv_header_includes_all_required_fields(self, client: AsyncClient) -> None:
        with patch(
            "src.api.operational_dashboard.get_operational_metrics",
            new=AsyncMock(return_value=_make_metrics()),
        ):
            response = await client.get("/api/admin/operational-dashboard/export/metrics")
        header = response.text.strip().split("\n")[0]
        for field in ("period_days", "capacity", "current_count", "intake_count", "outcome_count"):
            assert field in header


# ---------------------------------------------------------------------------
# /export/population tests
# ---------------------------------------------------------------------------


class TestExportPopulationCsv:
    @pytest.mark.asyncio
    async def test_returns_200_with_csv_content_type(self, client: AsyncClient) -> None:
        with patch(
            "src.api.operational_dashboard.get_operational_metrics",
            new=AsyncMock(return_value=_make_metrics()),
        ):
            response = await client.get("/api/admin/operational-dashboard/export/population")
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_content_disposition_header(self, client: AsyncClient) -> None:
        with patch(
            "src.api.operational_dashboard.get_operational_metrics",
            new=AsyncMock(return_value=_make_metrics()),
        ):
            response = await client.get("/api/admin/operational-dashboard/export/population")
        assert "dashboard-population.csv" in response.headers.get("content-disposition", "")

    @pytest.mark.asyncio
    async def test_csv_has_header_and_seven_status_rows(self, client: AsyncClient) -> None:
        with patch(
            "src.api.operational_dashboard.get_operational_metrics",
            new=AsyncMock(return_value=_make_metrics()),
        ):
            response = await client.get("/api/admin/operational-dashboard/export/population")
        lines = response.text.strip().split("\n")
        # 1 header + 7 status rows (intake, quarantine, available, foster, under_treatment, adopted, deceased)
        assert len(lines) == 8

    @pytest.mark.asyncio
    async def test_csv_contains_all_statuses(self, client: AsyncClient) -> None:
        with patch(
            "src.api.operational_dashboard.get_operational_metrics",
            new=AsyncMock(return_value=_make_metrics()),
        ):
            response = await client.get("/api/admin/operational-dashboard/export/population")
        for status in (
            "intake",
            "quarantine",
            "available",
            "foster",
            "under_treatment",
            "adopted",
            "deceased",
        ):
            assert status in response.text

    @pytest.mark.asyncio
    async def test_csv_header_includes_required_fields(self, client: AsyncClient) -> None:
        with patch(
            "src.api.operational_dashboard.get_operational_metrics",
            new=AsyncMock(return_value=_make_metrics()),
        ):
            response = await client.get("/api/admin/operational-dashboard/export/population")
        header = response.text.strip().split("\n")[0]
        assert "status" in header
        assert "count" in header
        assert "occupancy_contribution" in header

    @pytest.mark.asyncio
    async def test_csv_contains_generated_at(self, client: AsyncClient) -> None:
        with patch(
            "src.api.operational_dashboard.get_operational_metrics",
            new=AsyncMock(return_value=_make_metrics()),
        ):
            response = await client.get("/api/admin/operational-dashboard/export/population")
        assert "2026-03-29" in response.text
