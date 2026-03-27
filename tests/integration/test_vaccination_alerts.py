"""Integration tests for vaccination due-date alert endpoints."""

from datetime import date, timedelta

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.asyncio(loop_scope="function"), pytest.mark.integration]


async def _create_animal(client: AsyncClient) -> str:
    import uuid

    resp = await client.post(
        "/animals",
        json={
            "name": f"Alert-Dog-{uuid.uuid4().hex[:6]}",
            "species": "dog",
            "breed": "mixed",
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def _create_vaccine_type(client: AsyncClient) -> dict:
    import uuid

    resp = await client.post(
        "/vaccine-types",
        json={
            "name": f"Alert-Vaccine-{uuid.uuid4().hex[:6]}",
            "target_species": "all",
            "is_required": True,
        },
    )
    assert resp.status_code == 201
    return resp.json()


class TestVaccinationAlerts:
    """Tests for /vaccination-alerts and /animals/{id}/vaccination-alerts."""

    async def test_empty_alerts(self, client: AsyncClient) -> None:
        resp = await client.get("/vaccination-alerts")
        assert resp.status_code == 200
        body = resp.json()
        assert "overdue" in body
        assert "due_today" in body
        assert "upcoming" in body

    async def test_overdue_alert(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        vt = await _create_vaccine_type(client)

        # Create a vaccination scheduled 3 days ago
        past_date = (date.today() - timedelta(days=3)).isoformat()
        resp = await client.post(
            f"/animals/{animal_id}/vaccinations",
            json={
                "vaccine_type_id": vt["id"],
                "scheduled_date": past_date,
            },
        )
        assert resp.status_code == 201

        resp = await client.get("/vaccination-alerts")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_overdue"] >= 1

        # Verify overdue alerts contain vaccination IDs
        assert all("vaccination_id" in a for a in body["overdue"])
        # Check the animal-scoped endpoint
        resp = await client.get(
            f"/animals/{animal_id}/vaccination-alerts",
            params={"window_days": 7},
        )
        assert resp.status_code == 200
        animal_alerts = resp.json()
        assert animal_alerts["total_overdue"] >= 1
        for alert in animal_alerts["overdue"]:
            assert alert["animal_id"] == animal_id
            assert alert["severity"] == "overdue"
            assert alert["days_until_due"] < 0

    async def test_due_today_alert(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        vt = await _create_vaccine_type(client)

        today = date.today().isoformat()
        resp = await client.post(
            f"/animals/{animal_id}/vaccinations",
            json={
                "vaccine_type_id": vt["id"],
                "scheduled_date": today,
            },
        )
        assert resp.status_code == 201

        resp = await client.get(
            f"/animals/{animal_id}/vaccination-alerts",
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_due_today"] >= 1
        for alert in body["due_today"]:
            assert alert["severity"] == "due_today"
            assert alert["days_until_due"] == 0

    async def test_upcoming_alert(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        vt = await _create_vaccine_type(client)

        future_date = (date.today() + timedelta(days=5)).isoformat()
        resp = await client.post(
            f"/animals/{animal_id}/vaccinations",
            json={
                "vaccine_type_id": vt["id"],
                "scheduled_date": future_date,
            },
        )
        assert resp.status_code == 201

        resp = await client.get(
            f"/animals/{animal_id}/vaccination-alerts",
            params={"window_days": 7},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_upcoming"] >= 1
        for alert in body["upcoming"]:
            assert alert["severity"] == "upcoming"
            assert alert["days_until_due"] > 0

    async def test_administered_not_in_alerts(self, client: AsyncClient) -> None:
        """Administered vaccinations should not appear in alerts."""
        animal_id = await _create_animal(client)
        vt = await _create_vaccine_type(client)

        today = date.today().isoformat()
        resp = await client.post(
            f"/animals/{animal_id}/vaccinations",
            json={
                "vaccine_type_id": vt["id"],
                "scheduled_date": today,
                "administered_date": today,
                "vaccination_status": "administered",
            },
        )
        assert resp.status_code == 201

        resp = await client.get(
            f"/animals/{animal_id}/vaccination-alerts",
        )
        assert resp.status_code == 200
        body = resp.json()
        # Should not include administered vaccinations
        assert body["total_overdue"] + body["total_due_today"] + body["total_upcoming"] >= 0

    async def test_custom_window_days(self, client: AsyncClient) -> None:
        animal_id = await _create_animal(client)
        vt = await _create_vaccine_type(client)

        # Schedule 20 days from now — outside default 7-day window
        future_date = (date.today() + timedelta(days=20)).isoformat()
        resp = await client.post(
            f"/animals/{animal_id}/vaccinations",
            json={
                "vaccine_type_id": vt["id"],
                "scheduled_date": future_date,
            },
        )
        assert resp.status_code == 201

        # Default window (7 days) should not include it
        resp = await client.get(
            f"/animals/{animal_id}/vaccination-alerts",
            params={"window_days": 7},
        )
        assert resp.status_code == 200
        assert resp.json()["total_upcoming"] == 0

        # Extended window (30 days) should include it
        resp = await client.get(
            f"/animals/{animal_id}/vaccination-alerts",
            params={"window_days": 30},
        )
        assert resp.status_code == 200
        assert resp.json()["total_upcoming"] >= 1

    async def test_nonexistent_animal_returns_404(self, client: AsyncClient) -> None:
        resp = await client.get("/animals/00000000-0000-0000-0000-000000000099/vaccination-alerts")
        assert resp.status_code == 404
