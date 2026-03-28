"""Tests for community needs board API."""

import pytest
from fastapi import HTTPException
from src.api.community_needs import (
    NEED_TYPE_LABELS_ES,
    STATUS_LABELS_ES,
    URGENCY_LABELS_ES,
    ContactMethod,
    NeedCreateRequest,
    NeedStatus,
    NeedStatusUpdate,
    NeedType,
    RespondRequest,
    UrgencyLevel,
    _reset_store,
    create_need,
    get_community_need,
    list_community_needs,
    list_rescuer_needs,
    public_router,
    rescuer_router,
    respond_to_need,
    update_need_status,
)


@pytest.fixture(autouse=True)
def _clean_store() -> None:
    """Reset store before each test."""
    _reset_store()


def _sample_request(**kwargs: object) -> NeedCreateRequest:
    """Create a sample need request."""
    defaults = {
        "title": "Alimento urgente para 10 perros",
        "description": "Necesitamos alimento para 10 perros rescatados",
        "need_type": NeedType.FOOD,
        "urgency": UrgencyLevel.HIGH,
        "location": "Asuncion Centro",
        "contact_method": ContactMethod.WHATSAPP,
        "contact_info": "+595981123456",
    }
    defaults.update(kwargs)
    return NeedCreateRequest(**defaults)


# ---------------------------------------------------------------------------
# Enum tests
# ---------------------------------------------------------------------------


class TestEnums:
    """Verify enum members and labels."""

    def test_need_type_members(self) -> None:
        assert len(NeedType) == 6

    def test_urgency_members(self) -> None:
        assert len(UrgencyLevel) == 4

    def test_need_status_members(self) -> None:
        assert set(NeedStatus) == {
            NeedStatus.OPEN,
            NeedStatus.FULFILLED,
            NeedStatus.CANCELLED,
        }

    def test_contact_method_members(self) -> None:
        assert len(ContactMethod) == 3

    def test_need_type_labels_cover_all(self) -> None:
        for nt in NeedType:
            assert nt.value in NEED_TYPE_LABELS_ES

    def test_urgency_labels_cover_all(self) -> None:
        for u in UrgencyLevel:
            assert u.value in URGENCY_LABELS_ES

    def test_status_labels_cover_all(self) -> None:
        for s in NeedStatus:
            assert s.value in STATUS_LABELS_ES


# ---------------------------------------------------------------------------
# Router config tests
# ---------------------------------------------------------------------------


class TestRouterConfig:
    """Verify router setup."""

    def test_public_router_prefix(self) -> None:
        assert public_router.prefix == "/api/community/needs"

    def test_rescuer_router_prefix(self) -> None:
        assert rescuer_router.prefix == "/api/portal/rescuer/needs"

    def test_public_router_tags(self) -> None:
        assert "community-needs" in public_router.tags

    def test_rescuer_router_tags(self) -> None:
        assert "rescuer-needs" in rescuer_router.tags


# ---------------------------------------------------------------------------
# Create need tests
# ---------------------------------------------------------------------------


class TestCreateNeed:
    """Test POST /api/portal/rescuer/needs."""

    @pytest.mark.asyncio
    async def test_create_success(self) -> None:
        req = _sample_request()
        result = await create_need(req)
        assert result.id
        assert result.title == req.title
        assert result.status == NeedStatus.OPEN

    @pytest.mark.asyncio
    async def test_creates_with_uuid(self) -> None:
        req = _sample_request()
        result = await create_need(req)
        assert len(result.id) == 36  # UUID format

    @pytest.mark.asyncio
    async def test_labels_populated(self) -> None:
        req = _sample_request()
        result = await create_need(req)
        assert result.need_type_label == "Alimento"
        assert result.urgency_label == "Alta"
        assert result.status_label == "Abierto"

    @pytest.mark.asyncio
    async def test_optional_cost(self) -> None:
        req = _sample_request(estimated_cost_pyg=500000)
        result = await create_need(req)
        assert result.estimated_cost_pyg == 500000

    @pytest.mark.asyncio
    async def test_responses_count_zero(self) -> None:
        req = _sample_request()
        result = await create_need(req)
        assert result.responses_count == 0


# ---------------------------------------------------------------------------
# List needs tests
# ---------------------------------------------------------------------------


class TestListCommunityNeeds:
    """Test GET /api/community/needs."""

    @pytest.mark.asyncio
    async def test_empty_list(self) -> None:
        result = await list_community_needs(
            need_type=None, urgency=None, location=None, page=1, page_size=20
        )
        assert result.total == 0
        assert len(result.needs) == 0

    @pytest.mark.asyncio
    async def test_returns_created_need(self) -> None:
        await create_need(_sample_request())
        result = await list_community_needs(
            need_type=None, urgency=None, location=None, page=1, page_size=20
        )
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_filter_by_type(self) -> None:
        await create_need(_sample_request(need_type=NeedType.FOOD))
        await create_need(_sample_request(need_type=NeedType.MEDICAL))
        result = await list_community_needs(
            need_type=NeedType.FOOD, urgency=None, location=None, page=1, page_size=20
        )
        assert result.total == 1
        assert result.needs[0].need_type == NeedType.FOOD

    @pytest.mark.asyncio
    async def test_filter_by_urgency(self) -> None:
        await create_need(_sample_request(urgency=UrgencyLevel.CRITICAL))
        await create_need(_sample_request(urgency=UrgencyLevel.LOW))
        result = await list_community_needs(
            need_type=None, urgency=UrgencyLevel.CRITICAL, location=None, page=1, page_size=20
        )
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_filter_by_location(self) -> None:
        await create_need(_sample_request(location="Asuncion Centro"))
        await create_need(_sample_request(location="San Lorenzo"))
        result = await list_community_needs(
            need_type=None, urgency=None, location="Asuncion", page=1, page_size=20
        )
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_urgency_ordering(self) -> None:
        await create_need(_sample_request(urgency=UrgencyLevel.LOW, title="Low"))
        await create_need(_sample_request(urgency=UrgencyLevel.CRITICAL, title="Critical"))
        result = await list_community_needs(
            need_type=None, urgency=None, location=None, page=1, page_size=20
        )
        assert result.needs[0].urgency == UrgencyLevel.CRITICAL

    @pytest.mark.asyncio
    async def test_excludes_fulfilled(self) -> None:
        req = _sample_request()
        need = await create_need(req)
        await update_need_status(need.id, NeedStatusUpdate(status=NeedStatus.FULFILLED))
        result = await list_community_needs(
            need_type=None, urgency=None, location=None, page=1, page_size=20
        )
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_pagination(self) -> None:
        for i in range(5):
            await create_need(_sample_request(title=f"Need {i}"))
        result = await list_community_needs(
            need_type=None, urgency=None, location=None, page=1, page_size=2
        )
        assert result.total == 5
        assert len(result.needs) == 2


# ---------------------------------------------------------------------------
# Get need detail tests
# ---------------------------------------------------------------------------


class TestGetCommunityNeed:
    """Test GET /api/community/needs/{need_id}."""

    @pytest.mark.asyncio
    async def test_get_existing(self) -> None:
        need = await create_need(_sample_request())
        result = await get_community_need(need.id)
        assert result.id == need.id

    @pytest.mark.asyncio
    async def test_not_found(self) -> None:
        with pytest.raises(HTTPException):
            await get_community_need("nonexistent")


# ---------------------------------------------------------------------------
# Respond to need tests
# ---------------------------------------------------------------------------


class TestRespondToNeed:
    """Test POST /api/community/needs/{need_id}/respond."""

    @pytest.mark.asyncio
    async def test_respond_success(self) -> None:
        need = await create_need(_sample_request())
        req = RespondRequest(
            responder_name="Juan",
            message="Tengo alimento disponible",
            contact_info="+595981999999",
        )
        result = await respond_to_need(need.id, req)
        assert result.response_id
        assert result.need_id == need.id

    @pytest.mark.asyncio
    async def test_respond_increments_count(self) -> None:
        need = await create_need(_sample_request())
        req = RespondRequest(
            responder_name="Juan",
            message="Puedo ayudar",
            contact_info="juan@email.com",
        )
        await respond_to_need(need.id, req)
        detail = await get_community_need(need.id)
        assert detail.responses_count == 1

    @pytest.mark.asyncio
    async def test_respond_to_nonexistent(self) -> None:
        req = RespondRequest(
            responder_name="Juan",
            message="Test",
            contact_info="test@test.com",
        )
        with pytest.raises(HTTPException):
            await respond_to_need("nonexistent", req)

    @pytest.mark.asyncio
    async def test_respond_to_fulfilled_fails(self) -> None:
        need = await create_need(_sample_request())
        await update_need_status(need.id, NeedStatusUpdate(status=NeedStatus.FULFILLED))
        req = RespondRequest(
            responder_name="Juan",
            message="Test",
            contact_info="test@test.com",
        )
        with pytest.raises(HTTPException):
            await respond_to_need(need.id, req)


# ---------------------------------------------------------------------------
# Update status tests
# ---------------------------------------------------------------------------


class TestUpdateNeedStatus:
    """Test PUT /api/portal/rescuer/needs/{need_id}."""

    @pytest.mark.asyncio
    async def test_mark_fulfilled(self) -> None:
        need = await create_need(_sample_request())
        result = await update_need_status(need.id, NeedStatusUpdate(status=NeedStatus.FULFILLED))
        assert result.status == NeedStatus.FULFILLED

    @pytest.mark.asyncio
    async def test_mark_cancelled(self) -> None:
        need = await create_need(_sample_request())
        result = await update_need_status(need.id, NeedStatusUpdate(status=NeedStatus.CANCELLED))
        assert result.status == NeedStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_update_nonexistent(self) -> None:
        with pytest.raises(HTTPException):
            await update_need_status("nonexistent", NeedStatusUpdate(status=NeedStatus.FULFILLED))


# ---------------------------------------------------------------------------
# Rescuer list tests
# ---------------------------------------------------------------------------


class TestListRescuerNeeds:
    """Test GET /api/portal/rescuer/needs."""

    @pytest.mark.asyncio
    async def test_empty_list(self) -> None:
        result = await list_rescuer_needs(page=1, page_size=20)
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_returns_own_needs(self) -> None:
        await create_need(_sample_request())
        result = await list_rescuer_needs(page=1, page_size=20)
        assert result.total == 1


# ---------------------------------------------------------------------------
# Frontend file assertions
# ---------------------------------------------------------------------------


class TestFrontendFile:
    """Verify frontend page exists."""

    def test_page_file_exists(self) -> None:
        from pathlib import Path

        page = Path("frontend/src/app/community/needs/page.tsx")
        assert page.exists(), "Frontend page must exist"
        content = page.read_text()
        assert "CommunityNeedsPage" in content
        assert "Necesidades de la comunidad" in content
