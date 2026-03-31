"""Tests for rescuer profile API."""

import pytest
from fastapi import HTTPException
from src.api.rescuer_profile import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    PROFILE_SLUGS,
    SAMPLE_PROFILES,
    AdoptionStatus,
    CampaignProgressStatus,
    VerificationMethod,
    get_contact_info,
    get_full_profile,
    get_rescuer_animals,
    get_rescuer_campaigns,
    get_supporters,
    router,
)

# -- Enum tests --------------------------------------------------------------


class TestEnums:
    def test_adoption_status_values(self):
        assert AdoptionStatus.AVAILABLE == "available"
        assert AdoptionStatus.IN_PROCESS == "in_process"
        assert AdoptionStatus.ADOPTED == "adopted"
        assert AdoptionStatus.MEDICAL_HOLD == "medical_hold"

    def test_campaign_progress_values(self):
        assert CampaignProgressStatus.ACTIVE == "active"
        assert CampaignProgressStatus.COMPLETED == "completed"
        assert CampaignProgressStatus.PAUSED == "paused"

    def test_verification_method_values(self):
        assert VerificationMethod.DOCUMENTS == "documents"
        assert VerificationMethod.SITE_VISIT == "site_visit"
        assert VerificationMethod.GOVERNMENT_REGISTRY == "government_registry"


# -- Constants tests ----------------------------------------------------------


class TestConstants:
    def test_default_page_size(self):
        assert DEFAULT_PAGE_SIZE == 12

    def test_max_page_size(self):
        assert MAX_PAGE_SIZE == 50

    def test_sample_profiles_not_empty(self):
        assert len(SAMPLE_PROFILES) > 0

    def test_profile_slugs_match_keys(self):
        assert list(SAMPLE_PROFILES.keys()) == PROFILE_SLUGS


# -- Router tests -------------------------------------------------------------


class TestRouter:
    def test_router_prefix(self):
        assert router.prefix == "/api/rescuers"

    def test_router_tags(self):
        assert "rescuer-profile" in router.tags


# -- Full profile tests -------------------------------------------------------


class TestFullProfile:
    @pytest.mark.asyncio
    async def test_get_carlos_profile(self):
        result = await get_full_profile("carlos-mendoza")
        assert result.header.display_name == "Carlos Mendoza"
        assert result.header.is_verified is True
        assert result.header.verification_method == VerificationMethod.SITE_VISIT
        assert result.impact.animals_rescued == 127
        assert result.impact.animals_adopted == 89
        assert len(result.animals_preview) <= 4
        assert len(result.campaigns) == 2
        assert result.contact.email == "carlos@rescate.py"

    @pytest.mark.asyncio
    async def test_get_laura_profile(self):
        result = await get_full_profile("laura-gimenez")
        assert result.header.display_name == "Laura Gimenez"
        assert result.impact.years_active == 10.2

    @pytest.mark.asyncio
    async def test_profile_not_found(self):
        with pytest.raises(HTTPException) as exc:
            await get_full_profile("nonexistent")
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_animals_preview_limited_to_four(self):
        result = await get_full_profile("carlos-mendoza")
        assert len(result.animals_preview) == 4

    @pytest.mark.asyncio
    async def test_profile_social_links(self):
        result = await get_full_profile("carlos-mendoza")
        assert "facebook" in result.header.social_links
        assert "instagram" in result.header.social_links

    @pytest.mark.asyncio
    async def test_support_options_present(self):
        result = await get_full_profile("carlos-mendoza")
        assert result.support_options.accepts_monthly is True
        assert result.support_options.custom_amount_allowed is True
        assert len(result.support_options.donation_options) > 0


# -- Animals tests ------------------------------------------------------------


class TestAnimals:
    @pytest.mark.asyncio
    async def test_list_all_animals(self):
        result = await get_rescuer_animals(
            "carlos-mendoza", page=1, page_size=12, adoption_status=None
        )
        assert result.total == 6
        assert len(result.animals) == 6

    @pytest.mark.asyncio
    async def test_filter_by_available(self):
        result = await get_rescuer_animals(
            "carlos-mendoza",
            page=1,
            page_size=12,
            adoption_status=AdoptionStatus.AVAILABLE,
        )
        assert result.total == 3
        for a in result.animals:
            assert a.adoption_status == AdoptionStatus.AVAILABLE

    @pytest.mark.asyncio
    async def test_filter_by_adopted(self):
        result = await get_rescuer_animals(
            "carlos-mendoza",
            page=1,
            page_size=12,
            adoption_status=AdoptionStatus.ADOPTED,
        )
        assert result.total == 1
        assert result.animals[0].name == "Simba"

    @pytest.mark.asyncio
    async def test_pagination(self):
        result = await get_rescuer_animals(
            "carlos-mendoza", page=1, page_size=2, adoption_status=None
        )
        assert len(result.animals) == 2
        assert result.total == 6

    @pytest.mark.asyncio
    async def test_animals_not_found_rescuer(self):
        with pytest.raises(HTTPException) as exc:
            await get_rescuer_animals("nonexistent", page=1, page_size=12, adoption_status=None)
        assert exc.value.status_code == 404


# -- Campaign tests -----------------------------------------------------------


class TestCampaigns:
    @pytest.mark.asyncio
    async def test_list_campaigns(self):
        result = await get_rescuer_campaigns("carlos-mendoza")
        assert result.total == 2
        assert result.campaigns[0].title == "Esterilizacion masiva Barrio Obrero"

    @pytest.mark.asyncio
    async def test_campaign_progress(self):
        result = await get_rescuer_campaigns("carlos-mendoza")
        active = [c for c in result.campaigns if c.status == CampaignProgressStatus.ACTIVE]
        assert len(active) == 1
        assert active[0].progress_pct == 65.0

    @pytest.mark.asyncio
    async def test_no_campaigns(self):
        result = await get_rescuer_campaigns("laura-gimenez")
        assert result.total == 0
        assert len(result.campaigns) == 0


# -- Supporters tests ---------------------------------------------------------


class TestSupporters:
    @pytest.mark.asyncio
    async def test_list_supporters(self):
        result = await get_supporters("carlos-mendoza", page=1, page_size=12)
        assert result.total == 5
        assert result.total_monthly == 3

    @pytest.mark.asyncio
    async def test_anonymous_supporter(self):
        result = await get_supporters("carlos-mendoza", page=1, page_size=12)
        anon = [s for s in result.supporters if s.is_anonymous]
        assert len(anon) == 1
        assert anon[0].amount is None

    @pytest.mark.asyncio
    async def test_pagination_supporters(self):
        result = await get_supporters("carlos-mendoza", page=1, page_size=2)
        assert len(result.supporters) == 2
        assert result.total == 5


# -- Contact tests ------------------------------------------------------------


class TestContact:
    @pytest.mark.asyncio
    async def test_get_contact(self):
        result = await get_contact_info("carlos-mendoza")
        assert result.email == "carlos@rescate.py"
        assert result.whatsapp == "+595981234567"
        assert result.accepts_messages is True

    @pytest.mark.asyncio
    async def test_contact_with_website(self):
        result = await get_contact_info("laura-gimenez")
        assert result.website_url == "https://refugioesperanza.com.py"

    @pytest.mark.asyncio
    async def test_contact_not_found(self):
        with pytest.raises(HTTPException) as exc:
            await get_contact_info("nonexistent")
        assert exc.value.status_code == 404


# -- Frontend test ------------------------------------------------------------


class TestFrontend:
    def test_frontend_page_exists(self):
        import os

        assert os.path.exists("frontend/src/app/rescuers/[slug]/page.tsx")
