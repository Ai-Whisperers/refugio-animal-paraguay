"""Volunteer driver registration API (RAP-620).

Provides endpoints for volunteer driver registration and management:
- Register as a volunteer driver
- List/search volunteer drivers
- Check driver availability
- Update driver profile and availability
- Verify/approve driver applications

Endpoints:
    POST /api/transport/drivers/                 -- register as volunteer driver
    GET  /api/transport/drivers/                  -- list/search drivers
    GET  /api/transport/drivers/available          -- get available drivers
    GET  /api/transport/drivers/{driver_id}        -- get driver details
    PUT  /api/transport/drivers/{driver_id}        -- update driver profile
    PUT  /api/transport/drivers/{driver_id}/availability -- update availability
    PUT  /api/transport/drivers/{driver_id}/verify      -- verify/reject driver
"""

import logging
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/transport/drivers",
    tags=["volunteer-drivers"],
)

MAX_DRIVERS_PER_PAGE = 100
DEFAULT_PAGE_SIZE = 20


class DriverStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class VehicleType(StrEnum):
    CAR = "car"
    SUV = "suv"
    VAN = "van"
    TRUCK = "truck"
    MOTORCYCLE = "motorcycle"


class AvailabilityDay(StrEnum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


STATUS_LABELS_ES: dict[str, str] = {
    DriverStatus.PENDING: "Pendiente",
    DriverStatus.VERIFIED: "Verificado",
    DriverStatus.ACTIVE: "Activo",
    DriverStatus.INACTIVE: "Inactivo",
    DriverStatus.SUSPENDED: "Suspendido",
}

VEHICLE_LABELS_ES: dict[str, str] = {
    VehicleType.CAR: "Auto",
    VehicleType.SUV: "Camioneta",
    VehicleType.VAN: "Furgoneta",
    VehicleType.TRUCK: "Camion",
    VehicleType.MOTORCYCLE: "Motocicleta",
}

DAY_LABELS_ES: dict[str, str] = {
    AvailabilityDay.MONDAY: "Lunes",
    AvailabilityDay.TUESDAY: "Martes",
    AvailabilityDay.WEDNESDAY: "Miercoles",
    AvailabilityDay.THURSDAY: "Jueves",
    AvailabilityDay.FRIDAY: "Viernes",
    AvailabilityDay.SATURDAY: "Sabado",
    AvailabilityDay.SUNDAY: "Domingo",
}


class AvailabilitySlot(BaseModel):
    day: AvailabilityDay
    start_time: str = Field(..., max_length=5)
    end_time: str = Field(..., max_length=5)


class DriverRegistration(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., max_length=200)
    phone: str = Field(..., max_length=30)
    vehicle_type: VehicleType
    vehicle_plate: str = Field(..., max_length=20)
    license_number: str = Field(..., max_length=50)
    has_animal_transport_box: bool = False
    max_animal_capacity: int = Field(default=1, ge=1, le=20)
    coverage_areas: list[str] = Field(default_factory=list)
    availability: list[AvailabilitySlot] = Field(default_factory=list)
    bio: str | None = Field(default=None, max_length=500)


class DriverResponse(BaseModel):
    id: str
    full_name: str
    email: str
    phone: str
    vehicle_type: VehicleType
    vehicle_plate: str
    license_number: str
    has_animal_transport_box: bool
    max_animal_capacity: int
    coverage_areas: list[str]
    availability: list[dict[str, Any]]
    bio: str | None
    status: DriverStatus
    admin_notes: str | None
    registered_at: str
    updated_at: str
    total_trips: int
    rating: float


class DriverListResponse(BaseModel):
    drivers: list[DriverResponse]
    total: int
    page: int
    page_size: int


class DriverUpdateRequest(BaseModel):
    phone: str | None = None
    vehicle_type: VehicleType | None = None
    vehicle_plate: str | None = None
    has_animal_transport_box: bool | None = None
    max_animal_capacity: int | None = None
    coverage_areas: list[str] | None = None
    bio: str | None = None


class AvailabilityUpdateRequest(BaseModel):
    availability: list[AvailabilitySlot]


class DriverVerifyRequest(BaseModel):
    verified: bool
    admin_notes: str | None = None


_drivers: dict[str, dict[str, Any]] = {}


def _reset_store() -> None:
    _drivers.clear()


def _build_response(record: dict[str, Any]) -> DriverResponse:
    return DriverResponse(
        id=record["id"],
        full_name=record["full_name"],
        email=record["email"],
        phone=record["phone"],
        vehicle_type=record["vehicle_type"],
        vehicle_plate=record["vehicle_plate"],
        license_number=record["license_number"],
        has_animal_transport_box=record["has_animal_transport_box"],
        max_animal_capacity=record["max_animal_capacity"],
        coverage_areas=record["coverage_areas"],
        availability=record["availability"],
        bio=record.get("bio"),
        status=record["status"],
        admin_notes=record.get("admin_notes"),
        registered_at=record["registered_at"],
        updated_at=record["updated_at"],
        total_trips=record.get("total_trips", 0),
        rating=record.get("rating", 0.0),
    )


@router.post("/", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
async def register_driver(registration: DriverRegistration) -> DriverResponse:
    for existing in _drivers.values():
        if existing["email"].lower() == registration.email.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Driver with email '{registration.email}' already registered",
            )
    now = datetime.now(UTC).isoformat()
    driver_id = str(uuid4())
    record: dict[str, Any] = {
        "id": driver_id,
        "full_name": registration.full_name,
        "email": registration.email,
        "phone": registration.phone,
        "vehicle_type": registration.vehicle_type,
        "vehicle_plate": registration.vehicle_plate,
        "license_number": registration.license_number,
        "has_animal_transport_box": registration.has_animal_transport_box,
        "max_animal_capacity": registration.max_animal_capacity,
        "coverage_areas": registration.coverage_areas,
        "availability": [slot.model_dump() for slot in registration.availability],
        "bio": registration.bio,
        "status": DriverStatus.PENDING,
        "admin_notes": None,
        "registered_at": now,
        "updated_at": now,
        "total_trips": 0,
        "rating": 0.0,
    }
    _drivers[driver_id] = record
    logger.info("Driver registered", extra={"driver_id": driver_id, "name": registration.full_name})
    return _build_response(record)


@router.get("/", response_model=DriverListResponse)
async def list_drivers(
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_DRIVERS_PER_PAGE),
    status_filter: DriverStatus | None = Query(None, alias="status"),
    vehicle_type: VehicleType | None = Query(None),
    search: str | None = Query(None, max_length=100),
) -> DriverListResponse:
    records = list(_drivers.values())
    if status_filter is not None:
        records = [r for r in records if r["status"] == status_filter]
    if vehicle_type is not None:
        records = [r for r in records if r["vehicle_type"] == vehicle_type]
    if search:
        search_lower = search.lower()
        records = [
            r
            for r in records
            if search_lower in r["full_name"].lower() or search_lower in r["email"].lower()
        ]
    records.sort(key=lambda r: r["registered_at"], reverse=True)
    total = len(records)
    start = (page - 1) * page_size
    page_records = records[start : start + page_size]
    return DriverListResponse(
        drivers=[_build_response(r) for r in page_records],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/available", response_model=list[DriverResponse])
async def get_available_drivers(
    day: AvailabilityDay | None = Query(None),
    vehicle_type: VehicleType | None = Query(None),
) -> list[DriverResponse]:
    eligible_statuses = {DriverStatus.VERIFIED, DriverStatus.ACTIVE}
    records = [r for r in _drivers.values() if r["status"] in eligible_statuses]
    if day is not None:
        records = [r for r in records if any(slot["day"] == day for slot in r["availability"])]
    if vehicle_type is not None:
        records = [r for r in records if r["vehicle_type"] == vehicle_type]
    return [_build_response(r) for r in records]


@router.get("/{driver_id}", response_model=DriverResponse)
async def get_driver(driver_id: str) -> DriverResponse:
    record = _drivers.get(driver_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Driver '{driver_id}' not found"
        )
    return _build_response(record)


@router.put("/{driver_id}", response_model=DriverResponse)
async def update_driver(driver_id: str, update: DriverUpdateRequest) -> DriverResponse:
    record = _drivers.get(driver_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Driver '{driver_id}' not found"
        )
    update_data = update.model_dump(exclude_none=True)
    for key, value in update_data.items():
        record[key] = value
    record["updated_at"] = datetime.now(UTC).isoformat()
    logger.info("Driver updated", extra={"driver_id": driver_id})
    return _build_response(record)


@router.put("/{driver_id}/availability", response_model=DriverResponse)
async def update_driver_availability(
    driver_id: str, request: AvailabilityUpdateRequest
) -> DriverResponse:
    record = _drivers.get(driver_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Driver '{driver_id}' not found"
        )
    record["availability"] = [slot.model_dump() for slot in request.availability]
    record["updated_at"] = datetime.now(UTC).isoformat()
    logger.info(
        "Driver availability updated",
        extra={"driver_id": driver_id, "slots": len(request.availability)},
    )
    return _build_response(record)


@router.put("/{driver_id}/verify", response_model=DriverResponse)
async def verify_driver(driver_id: str, request: DriverVerifyRequest) -> DriverResponse:
    record = _drivers.get(driver_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Driver '{driver_id}' not found"
        )
    if record["status"] != DriverStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Driver is not pending (current status: {record['status']})",
        )
    record["status"] = DriverStatus.VERIFIED if request.verified else DriverStatus.SUSPENDED
    if request.admin_notes:
        record["admin_notes"] = request.admin_notes
    record["updated_at"] = datetime.now(UTC).isoformat()
    logger.info(
        "Driver verification",
        extra={
            "driver_id": driver_id,
            "verified": request.verified,
            "new_status": record["status"],
        },
    )
    return _build_response(record)
