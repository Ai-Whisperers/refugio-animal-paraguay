"""Tests for trip tracking feature (RAP-622).

Covers:
    - Module structure and constants
    - Trip CRUD operations
    - Status transitions
    - Checkpoints and photos
    - Timeline generation
    - Frontend page structure and accessibility
"""

from pathlib import Path

import pytest
from fastapi import HTTPException

# ---------------------------------------------------------------------------
# Test: Module Structure
# ---------------------------------------------------------------------------


class TestModuleStructure:
    """Verify trip_tracking module exports and structure."""

    def test_module_imports(self) -> None:
        from src.api import trip_tracking

        assert hasattr(trip_tracking, "router")

    def test_router_has_prefix(self) -> None:
        from src.api.trip_tracking import router

        assert any(
            r.path.startswith("/api/transport/trips") for r in router.routes if hasattr(r, "path")
        )

    def test_router_has_tag(self) -> None:
        from src.api.trip_tracking import router

        assert "trip-tracking" in router.tags

    def test_trip_status_enum(self) -> None:
        from src.api.trip_tracking import TripStatus

        assert hasattr(TripStatus, "PLANNED")
        assert hasattr(TripStatus, "IN_TRANSIT")
        assert hasattr(TripStatus, "COMPLETED")
        assert hasattr(TripStatus, "CANCELLED")

    def test_checkpoint_type_enum(self) -> None:
        from src.api.trip_tracking import CheckpointType

        assert hasattr(CheckpointType, "DEPARTURE")
        assert hasattr(CheckpointType, "WAYPOINT")
        assert hasattr(CheckpointType, "ARRIVAL")

    def test_photo_type_enum(self) -> None:
        from src.api.trip_tracking import PhotoType

        assert hasattr(PhotoType, "ANIMAL_CONDITION")
        assert hasattr(PhotoType, "VEHICLE")
        assert hasattr(PhotoType, "CHECKPOINT")


# ---------------------------------------------------------------------------
# Test: Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify constants are properly defined."""

    def test_max_photos_per_trip(self) -> None:
        from src.api.trip_tracking import MAX_PHOTOS_PER_TRIP

        assert MAX_PHOTOS_PER_TRIP == 50

    def test_max_checkpoints_per_trip(self) -> None:
        from src.api.trip_tracking import MAX_CHECKPOINTS_PER_TRIP

        assert MAX_CHECKPOINTS_PER_TRIP == 100

    def test_max_note_length(self) -> None:
        from src.api.trip_tracking import MAX_NOTE_LENGTH

        assert MAX_NOTE_LENGTH == 1000

    def test_status_labels_spanish(self) -> None:
        from src.api.trip_tracking import TRIP_STATUS_LABELS_ES

        assert "planned" in TRIP_STATUS_LABELS_ES
        assert "in_transit" in TRIP_STATUS_LABELS_ES
        assert len(TRIP_STATUS_LABELS_ES) == 10

    def test_valid_transitions_defined(self) -> None:
        from src.api.trip_tracking import VALID_TRANSITIONS

        assert "planned" in VALID_TRANSITIONS
        assert "completed" in VALID_TRANSITIONS
        assert VALID_TRANSITIONS["completed"] == []


# ---------------------------------------------------------------------------
# Test: Status Transitions
# ---------------------------------------------------------------------------


class TestStatusTransitions:
    """Verify status transition rules."""

    def test_planned_can_go_to_driver_assigned(self) -> None:
        from src.api.trip_tracking import VALID_TRANSITIONS

        assert "driver_assigned" in VALID_TRANSITIONS["planned"]

    def test_planned_can_be_cancelled(self) -> None:
        from src.api.trip_tracking import VALID_TRANSITIONS

        assert "cancelled" in VALID_TRANSITIONS["planned"]

    def test_completed_cannot_transition(self) -> None:
        from src.api.trip_tracking import VALID_TRANSITIONS

        assert VALID_TRANSITIONS["completed"] == []

    def test_cancelled_cannot_transition(self) -> None:
        from src.api.trip_tracking import VALID_TRANSITIONS

        assert VALID_TRANSITIONS["cancelled"] == []

    def test_in_transit_goes_to_arriving(self) -> None:
        from src.api.trip_tracking import VALID_TRANSITIONS

        assert "arriving" in VALID_TRANSITIONS["in_transit"]

    def test_full_happy_path_transitions(self) -> None:
        from src.api.trip_tracking import VALID_TRANSITIONS

        path = [
            "planned",
            "driver_assigned",
            "pickup_en_route",
            "at_pickup",
            "animal_loaded",
            "in_transit",
            "arriving",
            "delivered",
            "completed",
        ]
        for i in range(len(path) - 1):
            assert (
                path[i + 1] in VALID_TRANSITIONS[path[i]]
            ), f"{path[i]} -> {path[i+1]} should be valid"


# ---------------------------------------------------------------------------
# Test: API Endpoints
# ---------------------------------------------------------------------------


class TestAPIEndpoints:
    """Test API endpoint behavior."""

    def setup_method(self) -> None:
        from src.api.trip_tracking import _reset_store

        _reset_store()

    @pytest.mark.asyncio
    async def test_create_trip_planned(self) -> None:
        from src.api.trip_tracking import TripCreateRequest, create_trip

        req = TripCreateRequest(
            animal_name="Luna",
            pickup_location="Refugio Central, Asunción",
            delivery_location="Hogar adoptivo, San Lorenzo",
        )
        result = await create_trip(req)
        assert result.animal_name == "Luna"
        assert result.status == "planned"

    @pytest.mark.asyncio
    async def test_create_trip_with_driver(self) -> None:
        from src.api.trip_tracking import TripCreateRequest, create_trip

        req = TripCreateRequest(
            animal_name="Max",
            pickup_location="Veterinaria Sur",
            delivery_location="Refugio Norte",
            driver_name="Carlos",
            driver_phone="+595981000000",
        )
        result = await create_trip(req)
        assert result.status == "driver_assigned"
        assert result.driver_name == "Carlos"

    @pytest.mark.asyncio
    async def test_get_trip(self) -> None:
        from src.api.trip_tracking import TripCreateRequest, create_trip, get_trip

        created = await create_trip(
            TripCreateRequest(
                animal_name="Test",
                pickup_location="A",
                delivery_location="B",
            )
        )
        result = await get_trip(created.id)
        assert result.animal_name == "Test"

    @pytest.mark.asyncio
    async def test_get_trip_not_found(self) -> None:
        from src.api.trip_tracking import get_trip

        with pytest.raises(HTTPException) as exc_info:
            await get_trip("nonexistent")
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_status_valid(self) -> None:
        from src.api.trip_tracking import (
            StatusUpdateRequest,
            TripCreateRequest,
            TripStatus,
            create_trip,
            update_trip_status,
        )

        trip = await create_trip(
            TripCreateRequest(
                animal_name="Test",
                pickup_location="A",
                delivery_location="B",
            )
        )
        result = await update_trip_status(
            trip.id,
            StatusUpdateRequest(new_status=TripStatus.DRIVER_ASSIGNED),
        )
        assert result.status == "driver_assigned"

    @pytest.mark.asyncio
    async def test_update_status_invalid_transition(self) -> None:
        from src.api.trip_tracking import (
            StatusUpdateRequest,
            TripCreateRequest,
            TripStatus,
            create_trip,
            update_trip_status,
        )

        trip = await create_trip(
            TripCreateRequest(
                animal_name="Test",
                pickup_location="A",
                delivery_location="B",
            )
        )
        with pytest.raises(HTTPException) as exc_info:
            await update_trip_status(
                trip.id,
                StatusUpdateRequest(new_status=TripStatus.COMPLETED),
            )
        assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_add_checkpoint(self) -> None:
        from src.api.trip_tracking import (
            CheckpointRequest,
            CheckpointType,
            TripCreateRequest,
            add_checkpoint,
            create_trip,
        )

        trip = await create_trip(
            TripCreateRequest(
                animal_name="Test",
                pickup_location="A",
                delivery_location="B",
            )
        )
        result = await add_checkpoint(
            trip.id,
            CheckpointRequest(
                checkpoint_type=CheckpointType.DEPARTURE,
                location_name="Punto de salida",
            ),
        )
        assert result.location_name == "Punto de salida"

    @pytest.mark.asyncio
    async def test_add_photo(self) -> None:
        from src.api.trip_tracking import (
            PhotoType,
            PhotoUploadRequest,
            TripCreateRequest,
            add_photo,
            create_trip,
        )

        trip = await create_trip(
            TripCreateRequest(
                animal_name="Test",
                pickup_location="A",
                delivery_location="B",
            )
        )
        result = await add_photo(
            trip.id,
            PhotoUploadRequest(
                photo_url="https://example.com/photo.jpg",
                photo_type=PhotoType.ANIMAL_CONDITION,
                caption="Animal en buen estado",
            ),
        )
        assert result.photo_type == "animal_condition"

    @pytest.mark.asyncio
    async def test_get_timeline(self) -> None:
        from src.api.trip_tracking import (
            CheckpointRequest,
            CheckpointType,
            TripCreateRequest,
            add_checkpoint,
            create_trip,
            get_trip_timeline,
        )

        trip = await create_trip(
            TripCreateRequest(
                animal_name="Test",
                pickup_location="A",
                delivery_location="B",
            )
        )
        await add_checkpoint(
            trip.id,
            CheckpointRequest(
                checkpoint_type=CheckpointType.DEPARTURE,
                location_name="Start",
            ),
        )
        timeline = await get_trip_timeline(trip.id)
        assert timeline.total_events >= 2  # creation + checkpoint

    @pytest.mark.asyncio
    async def test_list_active_trips(self) -> None:
        from src.api.trip_tracking import (
            TripCreateRequest,
            create_trip,
            list_active_trips,
        )

        await create_trip(
            TripCreateRequest(
                animal_name="Active",
                pickup_location="A",
                delivery_location="B",
            )
        )
        result = await list_active_trips()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_trips(self) -> None:
        from src.api.trip_tracking import (
            TripCreateRequest,
            create_trip,
            list_trips,
        )

        await create_trip(
            TripCreateRequest(
                animal_name="T1",
                pickup_location="A",
                delivery_location="B",
            )
        )
        await create_trip(
            TripCreateRequest(
                animal_name="T2",
                pickup_location="C",
                delivery_location="D",
            )
        )
        result = await list_trips(status_filter=None, page=1, page_size=20)
        assert result.total == 2

    @pytest.mark.asyncio
    async def test_completed_trip_has_timestamp(self) -> None:
        from src.api.trip_tracking import (
            StatusUpdateRequest,
            TripCreateRequest,
            TripStatus,
            create_trip,
            update_trip_status,
        )

        trip = await create_trip(
            TripCreateRequest(
                animal_name="Test",
                pickup_location="A",
                delivery_location="B",
            )
        )
        # Walk through full path to completed
        for next_status in [
            TripStatus.DRIVER_ASSIGNED,
            TripStatus.PICKUP_EN_ROUTE,
            TripStatus.AT_PICKUP,
            TripStatus.ANIMAL_LOADED,
            TripStatus.IN_TRANSIT,
            TripStatus.ARRIVING,
            TripStatus.DELIVERED,
            TripStatus.COMPLETED,
        ]:
            trip = await update_trip_status(trip.id, StatusUpdateRequest(new_status=next_status))
        assert trip.status == "completed"
        assert trip.completed_at is not None


# ---------------------------------------------------------------------------
# Test: Frontend Page
# ---------------------------------------------------------------------------


class TestTrackingPage:
    """Verify frontend tracking page structure."""

    @pytest.fixture
    def page_content(self) -> str:
        page_path = Path("frontend/src/app/admin/transporte/seguimiento/page.tsx")
        assert page_path.exists(), f"Page not found: {page_path}"
        return page_path.read_text()

    def test_page_is_client_component(self, page_content: str) -> None:
        assert '"use client"' in page_content

    def test_page_has_trip_cards(self, page_content: str) -> None:
        assert "TripCard" in page_content

    def test_page_has_timeline_view(self, page_content: str) -> None:
        assert "TimelineView" in page_content

    def test_page_has_status_badge(self, page_content: str) -> None:
        assert "StatusBadge" in page_content

    def test_page_has_filter_buttons(self, page_content: str) -> None:
        assert "Activos" in page_content
        assert "Todos" in page_content

    def test_page_has_auto_refresh(self, page_content: str) -> None:
        assert "REFRESH_INTERVAL_MS" in page_content or "setInterval" in page_content

    def test_page_has_status_config(self, page_content: str) -> None:
        assert "STATUS_CONFIG" in page_content

    def test_page_has_spanish_labels(self, page_content: str) -> None:
        assert "Seguimiento" in page_content
        assert "transporte" in page_content.lower()

    def test_page_has_loading_skeleton(self, page_content: str) -> None:
        assert "LoadingSkeleton" in page_content

    def test_page_has_empty_state(self, page_content: str) -> None:
        assert "No hay viajes" in page_content

    def test_page_has_driver_info(self, page_content: str) -> None:
        assert "driver_name" in page_content
        assert "driver_phone" in page_content

    def test_page_shows_checkpoint_count(self, page_content: str) -> None:
        assert "checkpoint_count" in page_content

    def test_page_shows_photo_count(self, page_content: str) -> None:
        assert "photo_count" in page_content


# ---------------------------------------------------------------------------
# Test: Accessibility
# ---------------------------------------------------------------------------


class TestAccessibility:
    """Verify accessibility features."""

    @pytest.fixture
    def page_content(self) -> str:
        page_path = Path("frontend/src/app/admin/transporte/seguimiento/page.tsx")
        return page_path.read_text()

    def test_has_aria_labels(self, page_content: str) -> None:
        assert "aria-label" in page_content

    def test_has_aria_busy(self, page_content: str) -> None:
        assert "aria-busy" in page_content

    def test_has_role_alert(self, page_content: str) -> None:
        assert 'role="alert"' in page_content

    def test_has_role_status(self, page_content: str) -> None:
        assert 'role="status"' in page_content

    def test_has_role_list(self, page_content: str) -> None:
        assert 'role="list"' in page_content

    def test_has_aria_hidden(self, page_content: str) -> None:
        assert 'aria-hidden="true"' in page_content

    def test_has_min_touch_targets(self, page_content: str) -> None:
        assert "min-h-[44px]" in page_content

    def test_has_aria_pressed(self, page_content: str) -> None:
        assert "aria-pressed" in page_content

    def test_has_keyboard_navigation(self, page_content: str) -> None:
        assert "onKeyDown" in page_content
        assert "tabIndex" in page_content


# ---------------------------------------------------------------------------
# Test: App Registration
# ---------------------------------------------------------------------------


class TestAppRegistration:
    """Verify router is registered in app.py."""

    def test_router_imported_in_app(self) -> None:
        content = Path("src/app.py").read_text()
        assert "trip_tracking_router" in content
