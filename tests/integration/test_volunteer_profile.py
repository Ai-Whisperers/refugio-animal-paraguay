"""Integration tests for volunteer profile skills/availability API (RAP-641).

Tests the new PUT /api/volunteers/profile and GET /api/volunteers/profile/options
endpoints against the live test database.

Requires a running PostgreSQL instance (refugio_dev).
"""

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# GET /api/volunteers/profile/options
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_profile_options_returns_skills_and_availability(client: AsyncClient) -> None:
    """Public options endpoint returns skill list and availability windows."""
    response = await client.get("/api/volunteers/profile/options")
    assert response.status_code == 200
    body = response.json()
    assert "skills" in body
    assert "availability" in body
    assert isinstance(body["skills"], list)
    assert isinstance(body["availability"], list)
    assert len(body["skills"]) > 0
    assert len(body["availability"]) > 0
    assert "animal_care" in body["skills"]
    assert "flexible" in body["availability"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_profile_options_skills_are_sorted(client: AsyncClient) -> None:
    """Skills list is sorted alphabetically."""
    response = await client.get("/api/volunteers/profile/options")
    assert response.status_code == 200
    skills = response.json()["skills"]
    assert skills == sorted(skills)


# ---------------------------------------------------------------------------
# PUT /api/volunteers/profile — unauthenticated
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_profile_requires_auth(client: AsyncClient) -> None:
    """Updating profile without auth token returns 401."""
    # Remove auth header if present from client fixture
    resp = await client.put(
        "/api/volunteers/profile",
        json={"bio": "Test bio content here for test"},
        headers={"Authorization": ""},
    )
    assert resp.status_code in (401, 403, 422)


# ---------------------------------------------------------------------------
# PUT /api/volunteers/profile — no volunteer profile
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_profile_without_volunteer_record_returns_404(client: AsyncClient) -> None:
    """User with no volunteer application gets 404 on profile update."""
    # The default staff client does not have a volunteer profile
    response = await client.put(
        "/api/volunteers/profile",
        json={"bio": "I want to help animals at the shelter."},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Full flow: apply → update profile fields → verify
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_apply_then_update_profile_skills_and_bio(client: AsyncClient) -> None:
    """Volunteer can apply and then update skills, bio, and languages."""
    # Submit application
    apply_resp = await client.post(
        "/api/volunteers/apply",
        json={
            "motivation": "Me apasionan los animales rescatados y quiero contribuir activamente.",
            "skills": ["animal_care"],
            "availability": ["weekday_mornings"],
        },
    )
    # May already exist from a previous test run — 201 or 409
    assert apply_resp.status_code in (201, 409)

    # Update profile with bio + skills + languages
    update_resp = await client.put(
        "/api/volunteers/profile",
        json={
            "bio": "Tengo cinco años de experiencia cuidando animales callejeros.",
            "skills": ["animal_care", "photography", "social_media"],
            "availability": ["weekday_mornings", "weekend_afternoons"],
            "hours_per_week": 8,
            "languages_spoken": ["Español", "Inglés"],
        },
    )
    assert update_resp.status_code == 200
    body = update_resp.json()

    assert body["bio"] == "Tengo cinco años de experiencia cuidando animales callejeros."
    assert "photography" in body["skills"]
    assert "social_media" in body["skills"]
    assert "weekend_afternoons" in body["availability"]
    assert body["hours_per_week"] == 8
    assert "Español" in body["languages_spoken"]
    assert "Inglés" in body["languages_spoken"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_profile_partial_fields_preserves_others(client: AsyncClient) -> None:
    """Partial update only changes provided fields; others remain unchanged."""
    # First, make sure there's a profile (apply if needed)
    await client.post(
        "/api/volunteers/apply",
        json={
            "motivation": "Me apasionan los animales rescatados y quiero contribuir activamente.",
            "skills": ["animal_care"],
            "availability": ["weekday_mornings"],
        },
    )

    # Set initial state
    await client.put(
        "/api/volunteers/profile",
        json={
            "bio": "Bio inicial.",
            "skills": ["animal_care", "fundraising"],
            "languages_spoken": ["Español"],
        },
    )

    # Partial update: only change bio
    partial_resp = await client.put(
        "/api/volunteers/profile",
        json={"bio": "Bio actualizada."},
    )
    assert partial_resp.status_code == 200
    body = partial_resp.json()
    assert body["bio"] == "Bio actualizada."
    # Skills should remain from previous update
    assert "animal_care" in body["skills"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_profile_bio_max_length_validation(client: AsyncClient) -> None:
    """Bio exceeding 500 characters returns 422."""
    response = await client.put(
        "/api/volunteers/profile",
        json={"bio": "a" * 501},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_profile_hours_per_week_out_of_range(client: AsyncClient) -> None:
    """Hours per week outside 1-40 returns 422."""
    response = await client.put(
        "/api/volunteers/profile",
        json={"hours_per_week": 50},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_my_profile_includes_new_fields(client: AsyncClient) -> None:
    """GET /api/volunteers/me returns bio and languages_spoken fields."""
    # Ensure profile exists
    await client.post(
        "/api/volunteers/apply",
        json={
            "motivation": "Me apasionan los animales rescatados y quiero contribuir activamente.",
        },
    )

    # Set some values
    await client.put(
        "/api/volunteers/profile",
        json={
            "bio": "Voluntaria con experiencia en fotografía y redes sociales.",
            "languages_spoken": ["Español", "Guaraní"],
        },
    )

    me_resp = await client.get("/api/volunteers/me")
    assert me_resp.status_code == 200
    body = me_resp.json()
    assert "bio" in body
    assert "languages_spoken" in body
    assert isinstance(body["languages_spoken"], list)
