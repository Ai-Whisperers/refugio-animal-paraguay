"""Tests for the transport request module (RAP-619).

Covers module structure, constants, status transitions, API endpoints,
frontend page, accessibility, and app registration.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from fastapi import HTTPException


def _make_request_data() -> dict:
    """Helper to create valid transport request data."""
    from src.api.transport_request import (
        AnimalInfo,
        LocationInfo,
        RequestUrgency,
        TransportReason,
        TransportRequestCreate,
    )

    return TransportRequestCreate(
        reason=TransportReason.ADOPTION_DELIVERY,
        urgency=RequestUrgency.NORMAL,
        pickup=LocationInfo(
            address="Av. Espana 1234",
            city="Asuncion",
            contact_name="Juan Perez",
            contact_phone="0981123456",
        ),
        delivery=LocationInfo(
            address="Ruta 2, Km 30",
            city="San Lorenzo",
            contact_name="Maria Lopez",
            contact_phone="0971654321",
        ),
        animals=[AnimalInfo(name="Luna", species="Perro")],
        requester_name="Carlos Test",
        requester_phone="0991111111",
    )


# ---------------------------------------------------------------------------
# Module structure
# ---------------------------------------------------------------------------
class TestModuleStructure:
    """Verify module-level attributes."""

    def test_router_exists(self) -> None:
        from src.api.transport_request import router

        assert router is not None

    def test_router_prefix(self) -> None:
        from src.api.transport_request import router

        assert router.prefix == "/api/transport/requests"

    def test_router_tag(self) -> None:
        from src.api.transport_request import router

        assert "transport-requests" in router.tags

    def test_request_status_enum(self) -> None:
        from src.api.transport_request import RequestStatus

        assert hasattr(RequestStatus, "PENDING")
        assert hasattr(RequestStatus, "APPROVED")
        assert hasattr(RequestStatus, "COMPLETED")
        assert hasattr(RequestStatus, "CANCELLED")

    def test_request_urgency_enum(self) -> None:
        from src.api.transport_request import RequestUrgency

        assert hasattr(RequestUrgency, "EMERGENCY")
        assert hasattr(RequestUrgency, "NORMAL")

    def test_transport_reason_enum(self) -> None:
        from src.api.transport_request import TransportReason

        assert hasattr(TransportReason, "ADOPTION_DELIVERY")
        assert hasattr(TransportReason, "RESCUE")
        assert hasattr(TransportReason, "VET_APPOINTMENT")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
class TestConstants:
    """Verify named constants."""

    def test_max_animals(self) -> None:
        from src.api.transport_request import MAX_ANIMALS_PER_REQUEST

        assert MAX_ANIMALS_PER_REQUEST == 10

    def test_status_labels_spanish(self) -> None:
        from src.api.transport_request import STATUS_LABELS_ES

        assert len(STATUS_LABELS_ES) == 6

    def test_urgency_labels_spanish(self) -> None:
        from src.api.transport_request import URGENCY_LABELS_ES

        assert len(URGENCY_LABELS_ES) == 4

    def test_reason_labels_spanish(self) -> None:
        from src.api.transport_request import REASON_LABELS_ES

        assert len(REASON_LABELS_ES) == 7

    def test_valid_transitions_defined(self) -> None:
        from src.api.transport_request import VALID_STATUS_TRANSITIONS

        assert "pending" in VALID_STATUS_TRANSITIONS
        assert "completed" in VALID_STATUS_TRANSITIONS


# ---------------------------------------------------------------------------
# Status transitions
# ---------------------------------------------------------------------------
class TestStatusTransitions:
    """Validate status transition rules."""

    def test_pending_can_go_to_approved(self) -> None:
        from src.api.transport_request import VALID_STATUS_TRANSITIONS

        assert "approved" in VALID_STATUS_TRANSITIONS["pending"]

    def test_pending_can_be_cancelled(self) -> None:
        from src.api.transport_request import VALID_STATUS_TRANSITIONS

        assert "cancelled" in VALID_STATUS_TRANSITIONS["pending"]

    def test_completed_has_no_transitions(self) -> None:
        from src.api.transport_request import VALID_STATUS_TRANSITIONS

        assert VALID_STATUS_TRANSITIONS["completed"] == []

    def test_cancelled_has_no_transitions(self) -> None:
        from src.api.transport_request import VALID_STATUS_TRANSITIONS

        assert VALID_STATUS_TRANSITIONS["cancelled"] == []


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------
class TestAPIEndpoints:
    """Test API endpoint functions."""

    def setup_method(self) -> None:
        from src.api.transport_request import _reset_store

        _reset_store()

    def test_create_transport_request(self) -> None:
        from src.api.transport_request import create_transport_request

        req = _make_request_data()
        result = asyncio.get_event_loop().run_until_complete(create_transport_request(req))
        assert result.status == "pending"
        assert result.animal_count == 1
        assert result.reason_label  # has Spanish label

    def test_list_empty_requests(self) -> None:
        from src.api.transport_request import list_transport_requests

        result = asyncio.get_event_loop().run_until_complete(
            list_transport_requests(status_filter=None, urgency=None, page=1, page_size=20)
        )
        assert result.total == 0

    def test_list_after_create(self) -> None:
        from src.api.transport_request import (
            create_transport_request,
            list_transport_requests,
        )

        req = _make_request_data()
        asyncio.get_event_loop().run_until_complete(create_transport_request(req))
        result = asyncio.get_event_loop().run_until_complete(
            list_transport_requests(status_filter=None, urgency=None, page=1, page_size=20)
        )
        assert result.total == 1

    def test_get_request_by_id(self) -> None:
        from src.api.transport_request import (
            create_transport_request,
            get_transport_request,
        )

        req = _make_request_data()
        created = asyncio.get_event_loop().run_until_complete(create_transport_request(req))
        fetched = asyncio.get_event_loop().run_until_complete(get_transport_request(created.id))
        assert fetched.id == created.id

    def test_get_request_not_found(self) -> None:
        from src.api.transport_request import get_transport_request

        with pytest.raises(HTTPException) as exc_info:
            asyncio.get_event_loop().run_until_complete(get_transport_request("nonexistent"))
        assert exc_info.value.status_code == 404

    def test_update_status_valid(self) -> None:
        from src.api.transport_request import (
            StatusUpdateRequest,
            create_transport_request,
            update_request_status,
        )

        req = _make_request_data()
        created = asyncio.get_event_loop().run_until_complete(create_transport_request(req))
        update = StatusUpdateRequest(new_status="approved")
        result = asyncio.get_event_loop().run_until_complete(
            update_request_status(created.id, update)
        )
        assert result.status == "approved"

    def test_update_status_invalid_transition(self) -> None:
        from src.api.transport_request import (
            StatusUpdateRequest,
            create_transport_request,
            update_request_status,
        )

        req = _make_request_data()
        created = asyncio.get_event_loop().run_until_complete(create_transport_request(req))
        update = StatusUpdateRequest(new_status="completed")
        with pytest.raises(HTTPException) as exc_info:
            asyncio.get_event_loop().run_until_complete(update_request_status(created.id, update))
        assert exc_info.value.status_code == 400

    def test_cancel_request(self) -> None:
        from src.api.transport_request import (
            cancel_request,
            create_transport_request,
        )

        req = _make_request_data()
        created = asyncio.get_event_loop().run_until_complete(create_transport_request(req))
        result = asyncio.get_event_loop().run_until_complete(cancel_request(created.id))
        assert result.status == "cancelled"

    def test_cancel_already_completed_fails(self) -> None:
        from src.api.transport_request import (
            RequestStatus,
            _transport_requests,
            cancel_request,
            create_transport_request,
        )

        req = _make_request_data()
        created = asyncio.get_event_loop().run_until_complete(create_transport_request(req))
        _transport_requests[created.id]["status"] = RequestStatus.COMPLETED
        with pytest.raises(HTTPException) as exc_info:
            asyncio.get_event_loop().run_until_complete(cancel_request(created.id))
        assert exc_info.value.status_code == 400

    def test_get_stats_empty(self) -> None:
        from src.api.transport_request import get_request_stats

        result = asyncio.get_event_loop().run_until_complete(get_request_stats())
        assert result.total_requests == 0

    def test_get_stats_after_creates(self) -> None:
        from src.api.transport_request import (
            create_transport_request,
            get_request_stats,
        )

        req = _make_request_data()
        asyncio.get_event_loop().run_until_complete(create_transport_request(req))
        asyncio.get_event_loop().run_until_complete(create_transport_request(req))
        result = asyncio.get_event_loop().run_until_complete(get_request_stats())
        assert result.total_requests == 2
        assert result.pending == 2


# ---------------------------------------------------------------------------
# Frontend page
# ---------------------------------------------------------------------------
class TestTransportRequestPage:
    """Validate the frontend page."""

    @pytest.fixture(autouse=True)
    def _load_page(self) -> None:
        page_path = Path("frontend/src/app/admin/transporte/solicitudes/page.tsx")
        assert page_path.exists(), "Transport request page not found"
        self.content = page_path.read_text()

    def test_is_client_component(self) -> None:
        assert '"use client"' in self.content

    def test_has_page_title(self) -> None:
        assert "Solicitudes de Transporte" in self.content

    def test_has_form_component(self) -> None:
        assert "TransportRequestForm" in self.content

    def test_has_request_card(self) -> None:
        assert "RequestCard" in self.content

    def test_has_status_badges(self) -> None:
        assert "StatusBadge" in self.content

    def test_has_urgency_badges(self) -> None:
        assert "UrgencyBadge" in self.content

    def test_has_pickup_delivery_sections(self) -> None:
        assert "Recogida" in self.content
        assert "Entrega" in self.content

    def test_has_animal_management(self) -> None:
        assert "addAnimal" in self.content or "animals" in self.content

    def test_has_loading_state(self) -> None:
        assert "loading" in self.content.lower()

    def test_has_error_handling(self) -> None:
        assert "error" in self.content.lower()

    def test_has_create_button(self) -> None:
        assert "Nueva Solicitud" in self.content

    def test_has_filter_buttons(self) -> None:
        assert "statusFilter" in self.content


# ---------------------------------------------------------------------------
# Accessibility
# ---------------------------------------------------------------------------
class TestAccessibility:
    """Validate WCAG compliance patterns."""

    @pytest.fixture(autouse=True)
    def _load_page(self) -> None:
        page_path = Path("frontend/src/app/admin/transporte/solicitudes/page.tsx")
        self.content = page_path.read_text()

    def test_has_aria_labels(self) -> None:
        assert "aria-label" in self.content

    def test_has_role_attributes(self) -> None:
        assert 'role="' in self.content

    def test_has_alert_role(self) -> None:
        assert 'role="alert"' in self.content

    def test_has_list_roles(self) -> None:
        assert 'role="list"' in self.content

    def test_has_aria_expanded(self) -> None:
        assert "aria-expanded" in self.content

    def test_has_aria_pressed(self) -> None:
        assert "aria-pressed" in self.content

    def test_has_aria_busy(self) -> None:
        assert "aria-busy" in self.content

    def test_has_aria_required(self) -> None:
        assert "aria-required" in self.content or "required" in self.content

    def test_has_form_labels(self) -> None:
        assert "htmlFor" in self.content or "aria-label" in self.content

    def test_has_min_touch_targets(self) -> None:
        assert "min-h-[44px]" in self.content

    def test_has_semantic_headings(self) -> None:
        assert "<h1" in self.content


# ---------------------------------------------------------------------------
# App registration
# ---------------------------------------------------------------------------
class TestAppRegistration:
    """Verify router is registered."""

    def test_router_imported(self) -> None:
        app_content = Path("src/app.py").read_text()
        assert "transport_request_router" in app_content

    def test_router_included(self) -> None:
        app_content = Path("src/app.py").read_text()
        assert "application.include_router(transport_request_router)" in app_content
