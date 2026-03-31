"""Real-time trip tracking with photo updates for animal transport.

Provides live tracking of transport trips, including status updates,
location checkpoints, photo uploads, and estimated arrival times.

Endpoints:
    POST /api/transport/trips                     -- create trip
    GET  /api/transport/trips                     -- list trips (filterable)
    GET  /api/transport/trips/{id}                -- get trip details
    PUT  /api/transport/trips/{id}/status         -- update trip status
    POST /api/transport/trips/{id}/checkpoints    -- add checkpoint
    POST /api/transport/trips/{id}/photos         -- add photo update
    GET  /api/transport/trips/{id}/timeline       -- get trip timeline
    GET  /api/transport/trips/active              -- list active trips
"""

import logging
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/transport/trips", tags=["trip-tracking"])

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_PHOTOS_PER_TRIP = 50
MAX_CHECKPOINTS_PER_TRIP = 100
MAX_NOTE_LENGTH = 1000
MAX_PHOTO_URL_LENGTH = 500
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
PHOTO_CAPTION_MAX_LENGTH = 200


class TripStatus(StrEnum):
    """Trip lifecycle status."""

    PLANNED = "planned"
    DRIVER_ASSIGNED = "driver_assigned"
    PICKUP_EN_ROUTE = "pickup_en_route"
    AT_PICKUP = "at_pickup"
    ANIMAL_LOADED = "animal_loaded"
    IN_TRANSIT = "in_transit"
    ARRIVING = "arriving"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CheckpointType(StrEnum):
    """Types of trip checkpoints."""

    DEPARTURE = "departure"
    WAYPOINT = "waypoint"
    REST_STOP = "rest_stop"
    FUEL_STOP = "fuel_stop"
    VET_STOP = "vet_stop"
    ARRIVAL = "arrival"


class PhotoType(StrEnum):
    """Types of trip photos."""

    ANIMAL_CONDITION = "animal_condition"
    VEHICLE = "vehicle"
    PICKUP_LOCATION = "pickup_location"
    DELIVERY_LOCATION = "delivery_location"
    CHECKPOINT = "checkpoint"
    DOCUMENTATION = "documentation"


TRIP_STATUS_LABELS_ES: dict[str, str] = {
    "planned": "Planificado",
    "driver_assigned": "Conductor asignado",
    "pickup_en_route": "En camino a recogida",
    "at_pickup": "En punto de recogida",
    "animal_loaded": "Animal cargado",
    "in_transit": "En tránsito",
    "arriving": "Llegando",
    "delivered": "Entregado",
    "completed": "Completado",
    "cancelled": "Cancelado",
}

# Valid status transitions
VALID_TRANSITIONS: dict[str, list[str]] = {
    "planned": ["driver_assigned", "cancelled"],
    "driver_assigned": ["pickup_en_route", "cancelled"],
    "pickup_en_route": ["at_pickup", "cancelled"],
    "at_pickup": ["animal_loaded", "cancelled"],
    "animal_loaded": ["in_transit"],
    "in_transit": ["arriving"],
    "arriving": ["delivered"],
    "delivered": ["completed"],
    "completed": [],
    "cancelled": [],
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class TripCreateRequest(BaseModel):
    """Request to create a trip."""

    animal_name: str = Field(..., min_length=1, max_length=200)
    animal_id: str | None = Field(default=None, max_length=100)
    pickup_location: str = Field(..., min_length=1, max_length=500)
    delivery_location: str = Field(..., min_length=1, max_length=500)
    driver_name: str | None = Field(default=None, max_length=200)
    driver_phone: str | None = Field(default=None, max_length=50)
    scheduled_pickup: str | None = Field(default=None, max_length=50)
    estimated_duration_minutes: int | None = Field(default=None, ge=1, le=1440)
    notes: str | None = Field(default=None, max_length=MAX_NOTE_LENGTH)
    requester_name: str | None = Field(default=None, max_length=200)


class StatusUpdateRequest(BaseModel):
    """Request to update trip status."""

    new_status: TripStatus
    note: str | None = Field(default=None, max_length=MAX_NOTE_LENGTH)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class CheckpointRequest(BaseModel):
    """Request to add a checkpoint."""

    checkpoint_type: CheckpointType
    location_name: str = Field(..., min_length=1, max_length=300)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    note: str | None = Field(default=None, max_length=MAX_NOTE_LENGTH)


class PhotoUploadRequest(BaseModel):
    """Request to add a photo."""

    photo_url: str = Field(..., min_length=1, max_length=MAX_PHOTO_URL_LENGTH)
    photo_type: PhotoType
    caption: str | None = Field(default=None, max_length=PHOTO_CAPTION_MAX_LENGTH)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class TripResponse(BaseModel):
    """Trip detail response."""

    id: str
    animal_name: str
    animal_id: str | None = None
    pickup_location: str
    delivery_location: str
    driver_name: str | None = None
    driver_phone: str | None = None
    status: TripStatus
    status_label: str
    scheduled_pickup: str | None = None
    estimated_duration_minutes: int | None = None
    notes: str | None = None
    requester_name: str | None = None
    checkpoint_count: int
    photo_count: int
    created_at: str
    updated_at: str
    completed_at: str | None = None


class CheckpointResponse(BaseModel):
    """Checkpoint in trip timeline."""

    id: str
    checkpoint_type: CheckpointType
    location_name: str
    latitude: float | None = None
    longitude: float | None = None
    note: str | None = None
    created_at: str


class PhotoResponse(BaseModel):
    """Photo in trip."""

    id: str
    photo_url: str
    photo_type: PhotoType
    caption: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    created_at: str


class TimelineEvent(BaseModel):
    """Event in trip timeline."""

    event_type: str
    timestamp: str
    description: str
    details: dict[str, Any] = Field(default_factory=dict)


class TripTimeline(BaseModel):
    """Complete trip timeline."""

    trip_id: str
    events: list[TimelineEvent]
    total_events: int


class TripListResponse(BaseModel):
    """Paginated trip list."""

    trips: list[TripResponse]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

_trips: dict[str, dict[str, Any]] = {}
_checkpoints: dict[str, list[dict[str, Any]]] = {}
_photos: dict[str, list[dict[str, Any]]] = {}
_status_history: dict[str, list[dict[str, Any]]] = {}


def _reset_store() -> None:
    """Reset all stores (for testing)."""
    _trips.clear()
    _checkpoints.clear()
    _photos.clear()
    _status_history.clear()


def _build_trip_response(trip: dict[str, Any]) -> TripResponse:
    """Build trip response from stored data."""
    trip_id = trip["id"]
    return TripResponse(
        id=trip_id,
        animal_name=trip["animal_name"],
        animal_id=trip.get("animal_id"),
        pickup_location=trip["pickup_location"],
        delivery_location=trip["delivery_location"],
        driver_name=trip.get("driver_name"),
        driver_phone=trip.get("driver_phone"),
        status=trip["status"],
        status_label=TRIP_STATUS_LABELS_ES.get(trip["status"], trip["status"]),
        scheduled_pickup=trip.get("scheduled_pickup"),
        estimated_duration_minutes=trip.get("estimated_duration_minutes"),
        notes=trip.get("notes"),
        requester_name=trip.get("requester_name"),
        checkpoint_count=len(_checkpoints.get(trip_id, [])),
        photo_count=len(_photos.get(trip_id, [])),
        created_at=trip["created_at"],
        updated_at=trip["updated_at"],
        completed_at=trip.get("completed_at"),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
async def create_trip(request: TripCreateRequest) -> TripResponse:
    """Create a new transport trip."""
    now = datetime.now(UTC).isoformat()
    trip_id = str(uuid4())
    initial_status = TripStatus.DRIVER_ASSIGNED if request.driver_name else TripStatus.PLANNED

    trip: dict[str, Any] = {
        "id": trip_id,
        "animal_name": request.animal_name,
        "animal_id": request.animal_id,
        "pickup_location": request.pickup_location,
        "delivery_location": request.delivery_location,
        "driver_name": request.driver_name,
        "driver_phone": request.driver_phone,
        "status": initial_status,
        "scheduled_pickup": request.scheduled_pickup,
        "estimated_duration_minutes": request.estimated_duration_minutes,
        "notes": request.notes,
        "requester_name": request.requester_name,
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
    }
    _trips[trip_id] = trip
    _checkpoints[trip_id] = []
    _photos[trip_id] = []
    _status_history[trip_id] = [
        {
            "status": initial_status,
            "timestamp": now,
            "note": "Trip created",
        }
    ]

    logger.info("Trip created", extra={"trip_id": trip_id, "status": initial_status})
    return _build_trip_response(trip)


@router.get("", response_model=TripListResponse)
async def list_trips(
    status_filter: TripStatus | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
) -> TripListResponse:
    """List trips with optional status filter."""
    trips = list(_trips.values())
    if status_filter is not None:
        trips = [t for t in trips if t["status"] == status_filter]
    trips.sort(key=lambda t: t["updated_at"], reverse=True)
    total = len(trips)
    start = (page - 1) * page_size
    page_trips = trips[start : start + page_size]
    return TripListResponse(
        trips=[_build_trip_response(t) for t in page_trips],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/active", response_model=list[TripResponse])
async def list_active_trips() -> list[TripResponse]:
    """List all currently active trips."""
    terminal_statuses = {TripStatus.COMPLETED, TripStatus.CANCELLED}
    active = [t for t in _trips.values() if t["status"] not in terminal_statuses]
    active.sort(key=lambda t: t["updated_at"], reverse=True)
    return [_build_trip_response(t) for t in active]


@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(trip_id: str) -> TripResponse:
    """Get trip details."""
    trip = _trips.get(trip_id)
    if trip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip '{trip_id}' not found",
        )
    return _build_trip_response(trip)


@router.put("/{trip_id}/status", response_model=TripResponse)
async def update_trip_status(trip_id: str, request: StatusUpdateRequest) -> TripResponse:
    """Update trip status with validation of allowed transitions."""
    trip = _trips.get(trip_id)
    if trip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip '{trip_id}' not found",
        )

    current = trip["status"]
    target = request.new_status
    allowed = VALID_TRANSITIONS.get(current, [])
    if target not in allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(f"Cannot transition from '{current}' to '{target}'. " f"Allowed: {allowed}"),
        )

    now = datetime.now(UTC).isoformat()
    trip["status"] = target
    trip["updated_at"] = now

    if target in (TripStatus.COMPLETED, TripStatus.CANCELLED):
        trip["completed_at"] = now

    _status_history.setdefault(trip_id, []).append(
        {"status": target, "timestamp": now, "note": request.note}
    )

    logger.info(
        "Trip status updated",
        extra={"trip_id": trip_id, "from": current, "to": target},
    )
    return _build_trip_response(trip)


@router.post(
    "/{trip_id}/checkpoints",
    response_model=CheckpointResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_checkpoint(trip_id: str, request: CheckpointRequest) -> CheckpointResponse:
    """Add a checkpoint to a trip."""
    if trip_id not in _trips:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip '{trip_id}' not found",
        )

    checkpoints = _checkpoints.setdefault(trip_id, [])
    if len(checkpoints) >= MAX_CHECKPOINTS_PER_TRIP:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Maximum {MAX_CHECKPOINTS_PER_TRIP} checkpoints per trip",
        )

    now = datetime.now(UTC).isoformat()
    checkpoint_id = str(uuid4())
    checkpoint: dict[str, Any] = {
        "id": checkpoint_id,
        "checkpoint_type": request.checkpoint_type,
        "location_name": request.location_name,
        "latitude": request.latitude,
        "longitude": request.longitude,
        "note": request.note,
        "created_at": now,
    }
    checkpoints.append(checkpoint)
    _trips[trip_id]["updated_at"] = now

    return CheckpointResponse(**checkpoint)


@router.post(
    "/{trip_id}/photos",
    response_model=PhotoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_photo(trip_id: str, request: PhotoUploadRequest) -> PhotoResponse:
    """Add a photo update to a trip."""
    if trip_id not in _trips:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip '{trip_id}' not found",
        )

    photos = _photos.setdefault(trip_id, [])
    if len(photos) >= MAX_PHOTOS_PER_TRIP:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Maximum {MAX_PHOTOS_PER_TRIP} photos per trip",
        )

    now = datetime.now(UTC).isoformat()
    photo_id = str(uuid4())
    photo: dict[str, Any] = {
        "id": photo_id,
        "photo_url": request.photo_url,
        "photo_type": request.photo_type,
        "caption": request.caption,
        "latitude": request.latitude,
        "longitude": request.longitude,
        "created_at": now,
    }
    photos.append(photo)
    _trips[trip_id]["updated_at"] = now

    return PhotoResponse(**photo)


@router.get("/{trip_id}/timeline", response_model=TripTimeline)
async def get_trip_timeline(trip_id: str) -> TripTimeline:
    """Get chronological timeline of all trip events."""
    if trip_id not in _trips:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip '{trip_id}' not found",
        )

    events: list[TimelineEvent] = []

    for entry in _status_history.get(trip_id, []):
        label = TRIP_STATUS_LABELS_ES.get(entry["status"], entry["status"])
        events.append(
            TimelineEvent(
                event_type="status_change",
                timestamp=entry["timestamp"],
                description=f"Estado: {label}",
                details={"status": entry["status"], "note": entry.get("note")},
            )
        )

    for cp in _checkpoints.get(trip_id, []):
        events.append(
            TimelineEvent(
                event_type="checkpoint",
                timestamp=cp["created_at"],
                description=f"Punto de control: {cp['location_name']}",
                details={
                    "type": cp["checkpoint_type"],
                    "location": cp["location_name"],
                },
            )
        )

    for photo in _photos.get(trip_id, []):
        events.append(
            TimelineEvent(
                event_type="photo",
                timestamp=photo["created_at"],
                description=photo.get("caption") or "Foto agregada",
                details={
                    "type": photo["photo_type"],
                    "url": photo["photo_url"],
                },
            )
        )

    events.sort(key=lambda e: e.timestamp)

    return TripTimeline(
        trip_id=trip_id,
        events=events,
        total_events=len(events),
    )
