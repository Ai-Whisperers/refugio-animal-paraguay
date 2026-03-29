"""Integration tests for the operational dashboard API endpoint (RAP-250).

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_operational_dashboard.py
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.integration
async def test_metrics_requires_auth(unauthenticated_client: AsyncClient) -> None:
    response = await unauthenticated_client.get("/api/admin/operational-dashboard/metrics")
    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_metrics_returns_200(client: AsyncClient) -> None:
    response = await client.get("/api/admin/operational-dashboard/metrics")
    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.integration
async def test_metrics_has_all_top_level_keys(client: AsyncClient) -> None:
    response = await client.get("/api/admin/operational-dashboard/metrics")
    data = response.json()
    expected = {"generated_at", "population", "occupancy", "period", "species", "avg_los_days"}
    assert expected.issubset(data.keys())


@pytest.mark.asyncio
@pytest.mark.integration
async def test_population_has_all_status_fields(client: AsyncClient) -> None:
    response = await client.get("/api/admin/operational-dashboard/metrics")
    population = response.json()["population"]
    required = {
        "intake",
        "quarantine",
        "available",
        "foster",
        "under_treatment",
        "adopted",
        "deceased",
        "total",
    }
    assert required.issubset(population.keys())


@pytest.mark.asyncio
@pytest.mark.integration
async def test_population_counts_non_negative(client: AsyncClient) -> None:
    response = await client.get("/api/admin/operational-dashboard/metrics")
    population = response.json()["population"]
    for field in (
        "intake",
        "quarantine",
        "available",
        "foster",
        "under_treatment",
        "adopted",
        "deceased",
        "total",
    ):
        assert population[field] >= 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_total_equals_sum_of_sheltered(client: AsyncClient) -> None:
    response = await client.get("/api/admin/operational-dashboard/metrics")
    pop = response.json()["population"]
    expected_total = (
        pop["intake"]
        + pop["quarantine"]
        + pop["available"]
        + pop["foster"]
        + pop["under_treatment"]
    )
    assert pop["total"] == expected_total


@pytest.mark.asyncio
@pytest.mark.integration
async def test_occupancy_rate_consistent(client: AsyncClient) -> None:
    response = await client.get("/api/admin/operational-dashboard/metrics")
    occupancy = response.json()["occupancy"]
    if occupancy["capacity"] > 0:
        expected = round(occupancy["current_count"] / occupancy["capacity"] * 100, 1)
        assert occupancy["occupancy_rate_pct"] == expected


@pytest.mark.asyncio
@pytest.mark.integration
async def test_default_period_is_30_days(client: AsyncClient) -> None:
    response = await client.get("/api/admin/operational-dashboard/metrics")
    assert response.json()["period"]["period_days"] == 30


@pytest.mark.asyncio
@pytest.mark.integration
async def test_custom_period_days_respected(client: AsyncClient) -> None:
    response = await client.get("/api/admin/operational-dashboard/metrics?period_days=7")
    assert response.json()["period"]["period_days"] == 7


@pytest.mark.asyncio
@pytest.mark.integration
async def test_custom_capacity_accepted(client: AsyncClient) -> None:
    response = await client.get("/api/admin/operational-dashboard/metrics?capacity=150")
    assert response.status_code == 200
    assert response.json()["occupancy"]["capacity"] == 150


@pytest.mark.asyncio
@pytest.mark.integration
async def test_invalid_period_days_rejected(client: AsyncClient) -> None:
    response = await client.get("/api/admin/operational-dashboard/metrics?period_days=0")
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_period_days_over_max_rejected(client: AsyncClient) -> None:
    response = await client.get("/api/admin/operational-dashboard/metrics?period_days=366")
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_avg_los_non_negative(client: AsyncClient) -> None:
    response = await client.get("/api/admin/operational-dashboard/metrics")
    assert response.json()["avg_los_days"] >= 0.0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_generated_at_is_iso_string(client: AsyncClient) -> None:
    response = await client.get("/api/admin/operational-dashboard/metrics")
    generated_at = response.json()["generated_at"]
    assert "T" in generated_at


@pytest.mark.asyncio
@pytest.mark.integration
async def test_species_has_dog_cat_other(client: AsyncClient) -> None:
    response = await client.get("/api/admin/operational-dashboard/metrics")
    species = response.json()["species"]
    assert "dog" in species
    assert "cat" in species
    assert "other" in species
    for field in ("dog", "cat", "other"):
        assert species[field] >= 0
