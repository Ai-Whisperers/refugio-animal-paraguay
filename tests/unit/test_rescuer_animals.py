"""Tests for rescuer animal listing management API."""

import pytest
from fastapi import HTTPException
from src.api.rescuer_animals import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MAX_PHOTOS_PER_ANIMAL,
    RESCUER_SLUGS,
    SAMPLE_ANIMALS,
    URGENCY_ORDER,
    VALID_TRANSITIONS,
    AnimalStatus,
    Species,
    UrgencyLevel,
    _reset_store,
    add_adoption_story,
    add_animal,
    change_status,
    delete_animal,
    get_animal,
    list_my_animals,
    list_public_animals,
    portal_router,
    public_router,
    update_animal,
)


@pytest.fixture(autouse=True)
def _clean_store():
    """Reset store before each test."""
    _reset_store()
    yield
    _reset_store()


# -- Enum tests --------------------------------------------------------------


class TestEnums:
    def test_species_values(self):
        assert Species.DOG == "dog"
        assert Species.CAT == "cat"
        assert Species.OTHER == "other"

    def test_urgency_values(self):
        assert UrgencyLevel.LOW == "low"
        assert UrgencyLevel.CRITICAL == "critical"

    def test_animal_status_values(self):
        assert AnimalStatus.AVAILABLE == "available"
        assert AnimalStatus.ADOPTED == "adopted"
        assert AnimalStatus.IN_TREATMENT == "in_treatment"
        assert AnimalStatus.ARCHIVED == "archived"


# -- Constants tests ----------------------------------------------------------


class TestConstants:
    def test_default_page_size(self):
        assert DEFAULT_PAGE_SIZE == 12

    def test_max_page_size(self):
        assert MAX_PAGE_SIZE == 50

    def test_max_photos(self):
        assert MAX_PHOTOS_PER_ANIMAL == 5

    def test_urgency_order(self):
        assert URGENCY_ORDER["critical"] < URGENCY_ORDER["low"]

    def test_valid_transitions(self):
        assert "adopted" in VALID_TRANSITIONS["available"]
        assert "available" not in VALID_TRANSITIONS["archived"]

    def test_sample_animals_not_empty(self):
        assert len(SAMPLE_ANIMALS) > 0

    def test_rescuer_slugs_not_empty(self):
        assert len(RESCUER_SLUGS) > 0


# -- Router tests -------------------------------------------------------------


class TestRouters:
    def test_portal_router_prefix(self):
        assert portal_router.prefix == "/api/portal/rescuer/animals"

    def test_public_router_prefix(self):
        assert public_router.prefix == "/api/rescuers"

    def test_portal_router_tags(self):
        assert "rescuer-animals-portal" in portal_router.tags

    def test_public_router_tags(self):
        assert "rescuer-animals-public" in public_router.tags


# -- List animals tests -------------------------------------------------------


class TestListAnimals:
    @pytest.mark.asyncio
    async def test_list_all(self):
        result = await list_my_animals(
            status_filter=None, species_filter=None, page=1, page_size=20
        )
        assert result.total == len(SAMPLE_ANIMALS)

    @pytest.mark.asyncio
    async def test_filter_by_available(self):
        result = await list_my_animals(
            status_filter=AnimalStatus.AVAILABLE,
            species_filter=None,
            page=1,
            page_size=20,
        )
        for a in result.animals:
            assert a.status == AnimalStatus.AVAILABLE

    @pytest.mark.asyncio
    async def test_filter_by_species(self):
        result = await list_my_animals(
            status_filter=None, species_filter=Species.CAT, page=1, page_size=20
        )
        for a in result.animals:
            assert a.species == Species.CAT

    @pytest.mark.asyncio
    async def test_pagination(self):
        result = await list_my_animals(status_filter=None, species_filter=None, page=1, page_size=2)
        assert len(result.animals) == 2
        assert result.total == len(SAMPLE_ANIMALS)

    @pytest.mark.asyncio
    async def test_sorted_by_urgency(self):
        result = await list_my_animals(
            status_filter=None, species_filter=None, page=1, page_size=20
        )
        urgencies = [URGENCY_ORDER.get(a.urgency, 99) for a in result.animals]
        assert urgencies == sorted(urgencies)


# -- Add animal tests ---------------------------------------------------------


class TestAddAnimal:
    @pytest.mark.asyncio
    async def test_add_animal(self):
        from src.api.rescuer_animals import AnimalCreateRequest

        req = AnimalCreateRequest(
            name="Toby",
            species=Species.DOG,
            age="2 anos",
            description="Perro amigable rescatado del centro de Asuncion",
        )
        result = await add_animal(req)
        assert result.name == "Toby"
        assert result.species == Species.DOG
        assert result.status == AnimalStatus.AVAILABLE

    @pytest.mark.asyncio
    async def test_add_animal_too_many_photos(self):
        from src.api.rescuer_animals import AnimalCreateRequest

        req = AnimalCreateRequest(
            name="Test",
            species=Species.CAT,
            age="1 ano",
            description="Description that is long enough to pass validation",
            photo_urls=[f"/img/{i}.jpg" for i in range(6)],
        )
        with pytest.raises(HTTPException) as exc:
            await add_animal(req)
        assert exc.value.status_code == 400


# -- Get animal tests ---------------------------------------------------------


class TestGetAnimal:
    @pytest.mark.asyncio
    async def test_get_existing(self):
        result = await get_animal("ranim-001")
        assert result.name == "Luna"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self):
        with pytest.raises(HTTPException) as exc:
            await get_animal("nonexistent")
        assert exc.value.status_code == 404


# -- Update animal tests ------------------------------------------------------


class TestUpdateAnimal:
    @pytest.mark.asyncio
    async def test_update_name(self):
        from src.api.rescuer_animals import AnimalUpdateRequest

        req = AnimalUpdateRequest(name="Luna Nueva")
        result = await update_animal("ranim-001", req)
        assert result.name == "Luna Nueva"

    @pytest.mark.asyncio
    async def test_update_urgency(self):
        from src.api.rescuer_animals import AnimalUpdateRequest

        req = AnimalUpdateRequest(urgency=UrgencyLevel.HIGH)
        result = await update_animal("ranim-001", req)
        assert result.urgency == UrgencyLevel.HIGH

    @pytest.mark.asyncio
    async def test_update_too_many_photos(self):
        from src.api.rescuer_animals import AnimalUpdateRequest

        req = AnimalUpdateRequest(photo_urls=[f"/img/{i}.jpg" for i in range(6)])
        with pytest.raises(HTTPException) as exc:
            await update_animal("ranim-001", req)
        assert exc.value.status_code == 400


# -- Status change tests ------------------------------------------------------


class TestStatusChange:
    @pytest.mark.asyncio
    async def test_available_to_adopted(self):
        from src.api.rescuer_animals import StatusChangeRequest

        req = StatusChangeRequest(new_status=AnimalStatus.ADOPTED, reason="Found a home")
        result = await change_status("ranim-001", req)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_available_to_in_treatment(self):
        from src.api.rescuer_animals import StatusChangeRequest

        req = StatusChangeRequest(new_status=AnimalStatus.IN_TREATMENT)
        result = await change_status("ranim-001", req)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_invalid_transition(self):
        from src.api.rescuer_animals import StatusChangeRequest

        # archived -> available is not valid
        # First archive it
        req_archive = StatusChangeRequest(new_status=AnimalStatus.ARCHIVED)
        await change_status("ranim-001", req_archive)

        req = StatusChangeRequest(new_status=AnimalStatus.AVAILABLE)
        with pytest.raises(HTTPException) as exc:
            await change_status("ranim-001", req)
        assert exc.value.status_code == 400


# -- Delete animal tests ------------------------------------------------------


class TestDeleteAnimal:
    @pytest.mark.asyncio
    async def test_soft_delete(self):
        result = await delete_animal("ranim-001")
        assert result.success is True

        animal = await get_animal("ranim-001")
        assert animal.status == AnimalStatus.ARCHIVED


# -- Adoption story tests -----------------------------------------------------


class TestAdoptionStory:
    @pytest.mark.asyncio
    async def test_add_story_to_adopted(self):
        from src.api.rescuer_animals import AdoptionStoryRequest

        req = AdoptionStoryRequest(
            story_text="Simba encontro un hogar maravilloso con la familia Rodriguez",
            adopter_name="Familia Rodriguez",
        )
        result = await add_adoption_story("ranim-005", req)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_story_on_non_adopted(self):
        from src.api.rescuer_animals import AdoptionStoryRequest

        req = AdoptionStoryRequest(story_text="This should fail because animal is available")
        with pytest.raises(HTTPException) as exc:
            await add_adoption_story("ranim-001", req)
        assert exc.value.status_code == 400


# -- Public listing tests -----------------------------------------------------


class TestPublicListing:
    @pytest.mark.asyncio
    async def test_list_available_animals(self):
        result = await list_public_animals("carlos-mendoza", species=None, urgency=None)
        for a in result.animals:
            assert a.urgency in ["low", "medium", "high", "critical"]
        assert result.rescuer_name == "Carlos Mendoza"

    @pytest.mark.asyncio
    async def test_filter_by_species(self):
        result = await list_public_animals("carlos-mendoza", species=Species.CAT, urgency=None)
        for a in result.animals:
            assert a.species == Species.CAT

    @pytest.mark.asyncio
    async def test_filter_by_urgency(self):
        result = await list_public_animals(
            "carlos-mendoza", species=None, urgency=UrgencyLevel.HIGH
        )
        for a in result.animals:
            assert a.urgency == UrgencyLevel.HIGH

    @pytest.mark.asyncio
    async def test_sorted_by_urgency(self):
        result = await list_public_animals("carlos-mendoza", species=None, urgency=None)
        urgencies = [URGENCY_ORDER.get(a.urgency, 99) for a in result.animals]
        assert urgencies == sorted(urgencies)

    @pytest.mark.asyncio
    async def test_nonexistent_rescuer(self):
        with pytest.raises(HTTPException) as exc:
            await list_public_animals("nonexistent", species=None, urgency=None)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_only_available_shown(self):
        result = await list_public_animals("carlos-mendoza", species=None, urgency=None)
        # ranim-004 (in_treatment) and ranim-005 (adopted) should not appear
        ids = [a.id for a in result.animals]
        assert "ranim-004" not in ids
        assert "ranim-005" not in ids


# -- Frontend test ------------------------------------------------------------


class TestFrontend:
    def test_frontend_page_exists(self):
        import os

        assert os.path.exists("frontend/src/app/portal/rescuer/animals/page.tsx")
