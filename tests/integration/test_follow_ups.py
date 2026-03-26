"""Integration tests for post-adoption follow-up endpoints.

Tests the /follow-ups endpoints with a live PostgreSQL instance (refugio_dev).

Run: pytest -m integration tests/integration/test_follow_ups.py
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient


async def _create_approved_request(client: AsyncClient) -> tuple[str, str, str]:
    """Create an animal, adopter, adoption request, and approve it."""
    resp = await client.post("/animals", json={"name": "FollowUpDog", "species": "dog"})
    assert resp.status_code == 201
    animal_id = resp.json()["id"]

    email = f"followup-{uuid4().hex[:8]}@example.com"
    resp = await client.post(
        "/adopters",
        json={"full_name": "Follow Up Adopter", "email": email, "phone": "+595981222222"},
    )
    assert resp.status_code == 201
    adopter_id = resp.json()["id"]

    resp = await client.post(
        "/adoption-requests",
        json={"animal_id": animal_id, "adopter_id": adopter_id},
    )
    assert resp.status_code == 201
    request_id = resp.json()["id"]

    resp = await client.patch(
        f"/adoption-requests/{request_id}/status",
        json={"status": "approved"},
    )
    assert resp.status_code == 200

    return request_id, animal_id, adopter_id


class TestScheduleFollowUps:
    """Tests for POST /follow-ups/schedule/{request_id}."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_schedule_returns_201(self, client: AsyncClient) -> None:
        request_id, _, _ = await _create_approved_request(client)

        resp = await client.post(f"/follow-ups/schedule/{request_id}")
        assert resp.status_code == 201
        data = resp.json()
        assert len(data) == 4

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_schedule_creates_correct_day_offsets(self, client: AsyncClient) -> None:
        request_id, _, _ = await _create_approved_request(client)

        resp = await client.post(f"/follow-ups/schedule/{request_id}")
        data = resp.json()
        offsets = sorted(item["day_offset"] for item in data)
        assert offsets == [7, 30, 90, 365]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_schedule_idempotent(self, client: AsyncClient) -> None:
        request_id, _, _ = await _create_approved_request(client)

        resp1 = await client.post(f"/follow-ups/schedule/{request_id}")
        resp2 = await client.post(f"/follow-ups/schedule/{request_id}")

        assert resp1.status_code == 201
        assert resp2.status_code == 201
        # Second call returns same 4 follow-ups (idempotent)
        assert len(resp2.json()) == 4

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_schedule_for_pending_request_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post("/animals", json={"name": "PendingCat", "species": "cat"})
        animal_id = resp.json()["id"]

        email = f"pending-fu-{uuid4().hex[:8]}@example.com"
        resp = await client.post("/adopters", json={"full_name": "Pending Adopter", "email": email})
        adopter_id = resp.json()["id"]

        resp = await client.post(
            "/adoption-requests",
            json={"animal_id": animal_id, "adopter_id": adopter_id},
        )
        request_id = resp.json()["id"]

        resp = await client.post(f"/follow-ups/schedule/{request_id}")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_schedule_for_nonexistent_request_returns_404(self, client: AsyncClient) -> None:
        fake_id = str(uuid4())
        resp = await client.post(f"/follow-ups/schedule/{fake_id}")
        assert resp.status_code == 404


class TestSurveySubmission:
    """Tests for POST /follow-ups/{id}/survey."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_submit_survey(self, client: AsyncClient) -> None:
        request_id, _, _ = await _create_approved_request(client)

        # Schedule follow-ups
        resp = await client.post(f"/follow-ups/schedule/{request_id}")
        follow_up_id = resp.json()[0]["id"]

        # Submit survey
        resp = await client.post(
            f"/follow-ups/{follow_up_id}/survey",
            json={"welfare_score": 5, "satisfaction_score": 4, "comments": "Very happy"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["welfare_score"] == 5
        assert data["satisfaction_score"] == 4
        assert data["status"] == "completed"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_survey_for_nonexistent_follow_up_returns_404(self, client: AsyncClient) -> None:
        fake_id = str(uuid4())
        resp = await client.post(
            f"/follow-ups/{fake_id}/survey",
            json={"welfare_score": 3, "satisfaction_score": 3},
        )
        assert resp.status_code == 404


class TestReturnRecording:
    """Tests for POST /follow-ups/{id}/return."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_record_return(self, client: AsyncClient) -> None:
        request_id, _, _ = await _create_approved_request(client)

        resp = await client.post(f"/follow-ups/schedule/{request_id}")
        follow_up_id = resp.json()[0]["id"]

        resp = await client.post(
            f"/follow-ups/{follow_up_id}/return",
            json={"return_reason_code": "moved_away", "return_notes": "Family relocated"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["return_reason_code"] == "moved_away"
        assert data["return_date"] is not None


class TestListAndDetail:
    """Tests for GET /follow-ups and GET /follow-ups/{id}."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_list_follow_ups(self, client: AsyncClient) -> None:
        request_id, _, _ = await _create_approved_request(client)
        await client.post(f"/follow-ups/schedule/{request_id}")

        resp = await client.get(f"/follow-ups?adoption_request_id={request_id}")
        assert resp.status_code == 200
        assert len(resp.json()) == 4

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_single_follow_up(self, client: AsyncClient) -> None:
        request_id, _, _ = await _create_approved_request(client)
        resp = await client.post(f"/follow-ups/schedule/{request_id}")
        follow_up_id = resp.json()[0]["id"]

        resp = await client.get(f"/follow-ups/{follow_up_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == follow_up_id

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_nonexistent_follow_up_returns_404(self, client: AsyncClient) -> None:
        fake_id = str(uuid4())
        resp = await client.get(f"/follow-ups/{fake_id}")
        assert resp.status_code == 404


class TestOutcomeAnalytics:
    """Tests for GET /follow-ups/analytics/outcomes."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_outcomes_endpoint_returns_stats(self, client: AsyncClient) -> None:
        resp = await client.get("/follow-ups/analytics/outcomes")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_completed_adoptions" in data
        assert "success_rate_pct" in data
        assert "return_rate_by_species" in data
