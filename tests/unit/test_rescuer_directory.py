"""Tests for rescuer directory API."""

import pytest
from fastapi import HTTPException
from src.api.rescuer_directory import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    SAMPLE_RESCUERS,
    SORT_LABELS_ES,
    SPECIALTY_LABELS_ES,
    RescuerSpecialty,
    SortOption,
    get_rescuer_impact,
    get_rescuer_profile,
    list_rescuers,
    router,
)

# ---------------------------------------------------------------------------
# Enum tests
# ---------------------------------------------------------------------------


class TestEnums:
    """Verify enum members and labels."""

    def test_specialty_members(self) -> None:
        assert len(RescuerSpecialty) == 6

    def test_sort_option_members(self) -> None:
        assert len(SortOption) == 4

    def test_specialty_labels_cover_all(self) -> None:
        for s in RescuerSpecialty:
            assert s.value in SPECIALTY_LABELS_ES

    def test_sort_labels_cover_all(self) -> None:
        for s in SortOption:
            assert s.value in SORT_LABELS_ES


# ---------------------------------------------------------------------------
# Constants tests
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify constant values."""

    def test_default_page_size(self) -> None:
        assert DEFAULT_PAGE_SIZE == 12

    def test_max_page_size(self) -> None:
        assert MAX_PAGE_SIZE == 48

    def test_sample_rescuers_exist(self) -> None:
        assert len(SAMPLE_RESCUERS) >= 5


# ---------------------------------------------------------------------------
# Router config tests
# ---------------------------------------------------------------------------


class TestRouterConfig:
    """Verify router setup."""

    def test_router_prefix(self) -> None:
        assert router.prefix == "/api/rescuers"

    def test_router_tags(self) -> None:
        assert "rescuer-directory" in router.tags


# ---------------------------------------------------------------------------
# List rescuers tests
# ---------------------------------------------------------------------------


class TestListRescuers:
    """Test GET /api/rescuers."""

    @pytest.mark.asyncio
    async def test_returns_rescuers(self) -> None:
        result = await list_rescuers(
            search=None,
            specialty=None,
            location=None,
            sort=SortOption.ACTIVITY,
            page=1,
            page_size=12,
        )
        assert result.total > 0
        assert len(result.rescuers) > 0

    @pytest.mark.asyncio
    async def test_only_verified(self) -> None:
        result = await list_rescuers(
            search=None,
            specialty=None,
            location=None,
            sort=SortOption.ACTIVITY,
            page=1,
            page_size=50,
        )
        for r in result.rescuers:
            assert r.is_verified

    @pytest.mark.asyncio
    async def test_search_by_name(self) -> None:
        result = await list_rescuers(
            search="Gatitos",
            specialty=None,
            location=None,
            sort=SortOption.ACTIVITY,
            page=1,
            page_size=12,
        )
        assert result.total == 1
        assert "Gatitos" in result.rescuers[0].name

    @pytest.mark.asyncio
    async def test_filter_by_specialty(self) -> None:
        result = await list_rescuers(
            search=None,
            specialty=RescuerSpecialty.CATS,
            location=None,
            sort=SortOption.ACTIVITY,
            page=1,
            page_size=12,
        )
        for r in result.rescuers:
            assert r.specialty == RescuerSpecialty.CATS

    @pytest.mark.asyncio
    async def test_filter_by_location(self) -> None:
        result = await list_rescuers(
            search=None,
            specialty=None,
            location="Asuncion",
            sort=SortOption.ACTIVITY,
            page=1,
            page_size=12,
        )
        for r in result.rescuers:
            assert "asuncion" in r.location.lower()

    @pytest.mark.asyncio
    async def test_sort_by_supporters(self) -> None:
        result = await list_rescuers(
            search=None,
            specialty=None,
            location=None,
            sort=SortOption.SUPPORTERS,
            page=1,
            page_size=12,
        )
        counts = [r.supporter_count for r in result.rescuers]
        assert counts == sorted(counts, reverse=True)

    @pytest.mark.asyncio
    async def test_sort_by_animals_rescued(self) -> None:
        result = await list_rescuers(
            search=None,
            specialty=None,
            location=None,
            sort=SortOption.ANIMALS_RESCUED,
            page=1,
            page_size=12,
        )
        counts = [r.animals_rescued for r in result.rescuers]
        assert counts == sorted(counts, reverse=True)

    @pytest.mark.asyncio
    async def test_sort_by_name(self) -> None:
        result = await list_rescuers(
            search=None,
            specialty=None,
            location=None,
            sort=SortOption.NAME,
            page=1,
            page_size=12,
        )
        names = [r.name.lower() for r in result.rescuers]
        assert names == sorted(names)

    @pytest.mark.asyncio
    async def test_pagination(self) -> None:
        result = await list_rescuers(
            search=None,
            specialty=None,
            location=None,
            sort=SortOption.ACTIVITY,
            page=1,
            page_size=2,
        )
        assert result.total == len(SAMPLE_RESCUERS)
        assert len(result.rescuers) == 2

    @pytest.mark.asyncio
    async def test_cards_have_labels(self) -> None:
        result = await list_rescuers(
            search=None,
            specialty=None,
            location=None,
            sort=SortOption.ACTIVITY,
            page=1,
            page_size=12,
        )
        for r in result.rescuers:
            assert r.specialty_label


# ---------------------------------------------------------------------------
# Get profile tests
# ---------------------------------------------------------------------------


class TestGetProfile:
    """Test GET /api/rescuers/{id}."""

    @pytest.mark.asyncio
    async def test_get_existing(self) -> None:
        result = await get_rescuer_profile("rsc-001")
        assert result.id == "rsc-001"
        assert result.name == "Ana Lopez Rescates"

    @pytest.mark.asyncio
    async def test_profile_has_bio(self) -> None:
        result = await get_rescuer_profile("rsc-001")
        assert len(result.bio) > 0

    @pytest.mark.asyncio
    async def test_profile_has_social_links(self) -> None:
        result = await get_rescuer_profile("rsc-001")
        assert isinstance(result.social_links, dict)

    @pytest.mark.asyncio
    async def test_not_found(self) -> None:
        with pytest.raises(HTTPException):
            await get_rescuer_profile("nonexistent")


# ---------------------------------------------------------------------------
# Get impact tests
# ---------------------------------------------------------------------------


class TestGetImpact:
    """Test GET /api/rescuers/{id}/impact."""

    @pytest.mark.asyncio
    async def test_get_existing(self) -> None:
        result = await get_rescuer_impact("rsc-001")
        assert result.rescuer_id == "rsc-001"
        assert result.total_rescued > 0

    @pytest.mark.asyncio
    async def test_has_monthly_rescues(self) -> None:
        result = await get_rescuer_impact("rsc-001")
        assert len(result.monthly_rescues) > 0

    @pytest.mark.asyncio
    async def test_has_species_breakdown(self) -> None:
        result = await get_rescuer_impact("rsc-001")
        assert len(result.species_breakdown) > 0

    @pytest.mark.asyncio
    async def test_community_rating_valid(self) -> None:
        result = await get_rescuer_impact("rsc-001")
        assert 0 <= result.community_rating <= 5

    @pytest.mark.asyncio
    async def test_not_found(self) -> None:
        with pytest.raises(HTTPException):
            await get_rescuer_impact("nonexistent")


# ---------------------------------------------------------------------------
# Frontend file assertions
# ---------------------------------------------------------------------------


class TestFrontendFile:
    """Verify frontend page exists."""

    def test_page_file_exists(self) -> None:
        from pathlib import Path

        page = Path("frontend/src/app/rescuers/page.tsx")
        assert page.exists(), "Frontend page must exist"
        content = page.read_text()
        assert "RescuerDirectoryPage" in content
        assert "Directorio de rescatistas" in content
