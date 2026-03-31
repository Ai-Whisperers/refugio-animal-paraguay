"""Unit tests for volunteer driver registration API (RAP-620)."""

from pathlib import Path
from uuid import uuid4

import pytest
from src.api.volunteer_driver import (
    DAY_LABELS_ES,
    STATUS_LABELS_ES,
    VEHICLE_LABELS_ES,
    AvailabilityDay,
    AvailabilitySlot,
    AvailabilityUpdateRequest,
    DriverListResponse,
    DriverRegistration,
    DriverResponse,
    DriverStatus,
    DriverUpdateRequest,
    DriverVerifyRequest,
    VehicleType,
    _build_response,
    _drivers,
    _reset_store,
    get_available_drivers,
    get_driver,
    list_drivers,
    register_driver,
    router,
    update_driver,
    update_driver_availability,
    verify_driver,
)


@pytest.fixture(autouse=True)
def _clean_store():
    _reset_store()
    yield
    _reset_store()


def _sample_registration(**overrides) -> DriverRegistration:
    defaults = {
        "full_name": "Carlos Fernandez",
        "email": "carlos@example.com",
        "phone": "+595 981 123456",
        "vehicle_type": VehicleType.SUV,
        "vehicle_plate": "ABC-1234",
        "license_number": "PY-2024-56789",
        "has_animal_transport_box": True,
        "max_animal_capacity": 3,
        "coverage_areas": ["Asuncion", "Lambare", "San Lorenzo"],
        "availability": [
            AvailabilitySlot(day=AvailabilityDay.MONDAY, start_time="08:00", end_time="12:00"),
            AvailabilitySlot(day=AvailabilityDay.WEDNESDAY, start_time="14:00", end_time="18:00"),
        ],
        "bio": "Voluntario con experiencia en transporte de animales.",
    }
    defaults.update(overrides)
    return DriverRegistration(**defaults)


class TestDriverEnums:
    def test_driver_status_values(self):
        assert DriverStatus.PENDING == "pending"
        assert DriverStatus.VERIFIED == "verified"
        assert DriverStatus.ACTIVE == "active"
        assert DriverStatus.INACTIVE == "inactive"
        assert DriverStatus.SUSPENDED == "suspended"

    def test_vehicle_type_values(self):
        assert VehicleType.CAR == "car"
        assert VehicleType.SUV == "suv"
        assert VehicleType.VAN == "van"
        assert VehicleType.TRUCK == "truck"
        assert VehicleType.MOTORCYCLE == "motorcycle"

    def test_availability_day_count(self):
        assert len(AvailabilityDay) == 7

    def test_status_labels_spanish(self):
        assert len(STATUS_LABELS_ES) == len(DriverStatus)

    def test_vehicle_labels_spanish(self):
        assert len(VEHICLE_LABELS_ES) == len(VehicleType)

    def test_day_labels_spanish(self):
        assert len(DAY_LABELS_ES) == len(AvailabilityDay)


class TestDriverSchemas:
    def test_registration_defaults(self):
        reg = DriverRegistration(
            full_name="Test",
            email="test@example.com",
            phone="+595 981 000000",
            vehicle_type=VehicleType.CAR,
            vehicle_plate="XYZ-999",
            license_number="LIC-001",
        )
        assert reg.has_animal_transport_box is False
        assert reg.max_animal_capacity == 1
        assert reg.coverage_areas == []
        assert reg.availability == []
        assert reg.bio is None

    def test_availability_slot_creation(self):
        slot = AvailabilitySlot(day=AvailabilityDay.FRIDAY, start_time="09:00", end_time="17:00")
        assert slot.day == AvailabilityDay.FRIDAY

    def test_update_request_optional_fields(self):
        update = DriverUpdateRequest()
        assert update.phone is None
        assert update.vehicle_type is None

    def test_verify_request(self):
        req = DriverVerifyRequest(verified=True, admin_notes="OK")
        assert req.verified is True


class TestRouterConfig:
    def test_router_prefix(self):
        assert router.prefix == "/api/transport/drivers"

    def test_router_tags(self):
        assert "volunteer-drivers" in router.tags


class TestRegisterDriver:
    @pytest.mark.asyncio
    async def test_register_success(self):
        result = await register_driver(_sample_registration())
        assert isinstance(result, DriverResponse)
        assert result.full_name == "Carlos Fernandez"
        assert result.status == DriverStatus.PENDING

    @pytest.mark.asyncio
    async def test_register_generates_uuid(self):
        result = await register_driver(_sample_registration())
        assert len(result.id) == 36

    @pytest.mark.asyncio
    async def test_register_sets_timestamps(self):
        result = await register_driver(_sample_registration())
        assert result.registered_at is not None
        assert result.updated_at is not None

    @pytest.mark.asyncio
    async def test_register_duplicate_email_fails(self):
        await register_driver(_sample_registration())
        with pytest.raises(Exception) as exc_info:
            await register_driver(_sample_registration(full_name="Another"))
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_register_stores_in_memory(self):
        result = await register_driver(_sample_registration())
        assert result.id in _drivers


class TestListDrivers:
    @pytest.mark.asyncio
    async def test_list_empty(self):
        result = await list_drivers(
            page=1, page_size=20, status_filter=None, vehicle_type=None, search=None
        )
        assert isinstance(result, DriverListResponse)
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_list_returns_registered(self):
        await register_driver(_sample_registration())
        await register_driver(_sample_registration(full_name="Ana", email="ana@example.com"))
        result = await list_drivers(
            page=1, page_size=20, status_filter=None, vehicle_type=None, search=None
        )
        assert result.total == 2

    @pytest.mark.asyncio
    async def test_list_filter_by_status(self):
        await register_driver(_sample_registration())
        result = await list_drivers(
            page=1, page_size=20, status_filter=DriverStatus.PENDING, vehicle_type=None, search=None
        )
        assert result.total == 1
        result2 = await list_drivers(
            page=1, page_size=20, status_filter=DriverStatus.ACTIVE, vehicle_type=None, search=None
        )
        assert result2.total == 0

    @pytest.mark.asyncio
    async def test_list_filter_by_vehicle(self):
        await register_driver(_sample_registration(vehicle_type=VehicleType.VAN))
        result = await list_drivers(
            page=1, page_size=20, status_filter=None, vehicle_type=VehicleType.VAN, search=None
        )
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_list_search_by_name(self):
        await register_driver(_sample_registration())
        result = await list_drivers(
            page=1, page_size=20, status_filter=None, vehicle_type=None, search="Carlos"
        )
        assert result.total == 1
        result2 = await list_drivers(
            page=1, page_size=20, status_filter=None, vehicle_type=None, search="ZZZ"
        )
        assert result2.total == 0

    @pytest.mark.asyncio
    async def test_list_pagination(self):
        for i in range(5):
            await register_driver(
                _sample_registration(full_name=f"Driver {i}", email=f"d{i}@example.com")
            )
        result = await list_drivers(
            page=1, page_size=2, status_filter=None, vehicle_type=None, search=None
        )
        assert len(result.drivers) == 2
        assert result.total == 5


class TestGetDriver:
    @pytest.mark.asyncio
    async def test_get_existing(self):
        created = await register_driver(_sample_registration())
        result = await get_driver(created.id)
        assert result.id == created.id

    @pytest.mark.asyncio
    async def test_get_nonexistent(self):
        with pytest.raises(Exception) as exc_info:
            await get_driver(str(uuid4()))
        assert exc_info.value.status_code == 404


class TestUpdateDriver:
    @pytest.mark.asyncio
    async def test_update_phone(self):
        created = await register_driver(_sample_registration())
        result = await update_driver(created.id, DriverUpdateRequest(phone="+595 981 999999"))
        assert result.phone == "+595 981 999999"

    @pytest.mark.asyncio
    async def test_update_vehicle_type(self):
        created = await register_driver(_sample_registration())
        result = await update_driver(
            created.id, DriverUpdateRequest(vehicle_type=VehicleType.TRUCK)
        )
        assert result.vehicle_type == VehicleType.TRUCK

    @pytest.mark.asyncio
    async def test_update_nonexistent(self):
        with pytest.raises(Exception) as exc_info:
            await update_driver(str(uuid4()), DriverUpdateRequest(phone="x"))
        assert exc_info.value.status_code == 404


class TestUpdateAvailability:
    @pytest.mark.asyncio
    async def test_update_availability(self):
        created = await register_driver(_sample_registration())
        new_slots = AvailabilityUpdateRequest(
            availability=[
                AvailabilitySlot(day=AvailabilityDay.SATURDAY, start_time="06:00", end_time="12:00")
            ]
        )
        result = await update_driver_availability(created.id, new_slots)
        assert len(result.availability) == 1

    @pytest.mark.asyncio
    async def test_update_availability_nonexistent(self):
        with pytest.raises(Exception) as exc_info:
            await update_driver_availability(
                str(uuid4()), AvailabilityUpdateRequest(availability=[])
            )
        assert exc_info.value.status_code == 404


class TestVerifyDriver:
    @pytest.mark.asyncio
    async def test_verify_pending(self):
        created = await register_driver(_sample_registration())
        result = await verify_driver(
            created.id, DriverVerifyRequest(verified=True, admin_notes="OK")
        )
        assert result.status == DriverStatus.VERIFIED

    @pytest.mark.asyncio
    async def test_reject_pending(self):
        created = await register_driver(_sample_registration())
        result = await verify_driver(
            created.id, DriverVerifyRequest(verified=False, admin_notes="Missing docs")
        )
        assert result.status == DriverStatus.SUSPENDED

    @pytest.mark.asyncio
    async def test_verify_non_pending_fails(self):
        created = await register_driver(_sample_registration())
        await verify_driver(created.id, DriverVerifyRequest(verified=True))
        with pytest.raises(Exception) as exc_info:
            await verify_driver(created.id, DriverVerifyRequest(verified=True))
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_verify_nonexistent(self):
        with pytest.raises(Exception) as exc_info:
            await verify_driver(str(uuid4()), DriverVerifyRequest(verified=True))
        assert exc_info.value.status_code == 404


class TestGetAvailableDrivers:
    @pytest.mark.asyncio
    async def test_returns_only_verified(self):
        created = await register_driver(_sample_registration())
        await verify_driver(created.id, DriverVerifyRequest(verified=True))
        await register_driver(_sample_registration(full_name="Pending", email="p@example.com"))
        result = await get_available_drivers(day=None, vehicle_type=None)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_filter_by_day(self):
        created = await register_driver(_sample_registration())
        await verify_driver(created.id, DriverVerifyRequest(verified=True))
        result = await get_available_drivers(day=AvailabilityDay.MONDAY, vehicle_type=None)
        assert len(result) == 1
        result2 = await get_available_drivers(day=AvailabilityDay.SUNDAY, vehicle_type=None)
        assert len(result2) == 0

    @pytest.mark.asyncio
    async def test_filter_by_vehicle(self):
        created = await register_driver(_sample_registration(vehicle_type=VehicleType.VAN))
        await verify_driver(created.id, DriverVerifyRequest(verified=True))
        result = await get_available_drivers(day=None, vehicle_type=VehicleType.VAN)
        assert len(result) == 1


class TestBuildResponse:
    @pytest.mark.asyncio
    async def test_build_from_stored(self):
        created = await register_driver(_sample_registration())
        response = _build_response(_drivers[created.id])
        assert isinstance(response, DriverResponse)
        assert response.id == created.id


class TestFrontendPage:
    def test_file_exists(self):
        assert Path("frontend/src/app/admin/transporte/conductores/page.tsx").exists()

    def test_contains_use_client(self):
        content = Path("frontend/src/app/admin/transporte/conductores/page.tsx").read_text()
        assert '"use client"' in content

    def test_contains_driver_components(self):
        content = Path("frontend/src/app/admin/transporte/conductores/page.tsx").read_text()
        assert "DriverCard" in content

    def test_contains_form(self):
        content = Path("frontend/src/app/admin/transporte/conductores/page.tsx").read_text()
        assert "RegistrationForm" in content

    def test_contains_vehicle_types(self):
        content = Path("frontend/src/app/admin/transporte/conductores/page.tsx").read_text()
        assert "vehicle" in content.lower()

    def test_responsive_classes(self):
        content = Path("frontend/src/app/admin/transporte/conductores/page.tsx").read_text()
        assert "md:" in content
