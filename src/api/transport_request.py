"""Transport request creation form API (RAP-619).

Provides endpoints for creating and managing animal transport requests:
- Create new transport requests with pickup/delivery details
- List and filter transport requests by status/urgency
- Update request status
- Cancel requests
- Get request details with timeline

Endpoints
---------
POST /api/transport/requests                     -- create new request
GET  /api/transport/requests                     -- list requests
GET  /api/transport/requests/{id}                -- get request details
PUT  /api/transport/requests/{id}/status         -- update status
POST /api/transport/requests/{id}/cancel         -- cancel request
GET  /api/transport/requests/stats               -- request statistics
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/transport/requests",
    tags=["transport-requests"],
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_ANIMALS_PER_REQUEST = 10
MAX_NOTE_LENGTH = 1000
MAX_ADDRESS_LENGTH = 500
CONTACT_PHONE_MIN_LENGTH = 7
CONTACT_PHONE_MAX_LENGTH = 20

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class RequestStatus(StrEnum):
    """Transport request lifecycle status."""

    PENDING = "pending"
    APPROVED = "approved"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RequestUrgency(StrEnum):
    """Transport request urgency level."""

    EMERGENCY = "emergency"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class TransportReason(StrEnum):
    """Reason for the transport."""

    ADOPTION_DELIVERY = "adoption_delivery"
    VET_APPOINTMENT = "vet_appointment"
    RESCUE = "rescue"
    SHELTER_TRANSFER = "shelter_transfer"
    FOSTER_PLACEMENT = "foster_placement"
    RETURN_TO_SHELTER = "return_to_shelter"
    EVENT = "event"


STATUS_LABELS_ES: dict[str, str] = {
    "pending": "Pendiente",
    "approved": "Aprobado",
    "assigned": "Asignado",
    "in_progress": "En progreso",
    "completed": "Completado",
    "cancelled": "Cancelado",
}

URGENCY_LABELS_ES: dict[str, str] = {
    "emergency": "Emergencia",
    "high": "Alta",
    "normal": "Normal",
    "low": "Baja",
}

REASON_LABELS_ES: dict[str, str] = {
    "adoption_delivery": "Entrega de adopcion",
    "vet_appointment": "Cita veterinaria",
    "rescue": "Rescate",
    "shelter_transfer": "Transferencia entre refugios",
    "foster_placement": "Acogida temporal",
    "return_to_shelter": "Retorno al refugio",
    "event": "Evento",
}

VALID_STATUS_TRANSITIONS: dict[str, list[str]] = {
    "pending": ["approved", "cancelled"],
    "approved": ["assigned", "cancelled"],
    "assigned": ["in_progress", "cancelled"],
    "in_progress": ["completed", "cancelled"],
    "completed": [],
    "cancelled": [],
}

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class LocationInfo(BaseModel):
    """Pickup or delivery location."""

    address: str = Field(max_length=MAX_ADDRESS_LENGTH)
    city: str
    contact_name: str
    contact_phone: str = Field(
        min_length=CONTACT_PHONE_MIN_LENGTH, max_length=CONTACT_PHONE_MAX_LENGTH
    )
    notes: str | None = None


class AnimalInfo(BaseModel):
    """Animal being transported."""

    animal_id: str | None = None
    name: str
    species: str
    special_needs: str | None = None


class TransportRequestCreate(BaseModel):
    """Create a new transport request."""

    reason: TransportReason
    urgency: RequestUrgency = RequestUrgency.NORMAL
    pickup: LocationInfo
    delivery: LocationInfo
    animals: list[AnimalInfo] = Field(min_length=1, max_length=MAX_ANIMALS_PER_REQUEST)
    preferred_date: str | None = None
    preferred_time: str | None = None
    notes: str | None = Field(default=None, max_length=MAX_NOTE_LENGTH)
    requester_name: str
    requester_phone: str
    requester_email: str | None = None


class TransportRequestResponse(BaseModel):
    """Transport request response."""

    id: str
    reason: TransportReason
    reason_label: str
    urgency: RequestUrgency
    urgency_label: str
    status: RequestStatus
    status_label: str
    pickup: LocationInfo
    delivery: LocationInfo
    animals: list[AnimalInfo]
    animal_count: int
    preferred_date: str | None = None
    preferred_time: str | None = None
    notes: str | None = None
    requester_name: str
    requester_phone: str
    requester_email: str | None = None
    assigned_driver: str | None = None
    created_at: str
    updated_at: str


class TransportRequestList(BaseModel):
    """Paginated transport request list."""

    requests: list[TransportRequestResponse]
    total: int
    page: int
    page_size: int


class StatusUpdateRequest(BaseModel):
    """Status update for a transport request."""

    new_status: RequestStatus
    note: str | None = None


class RequestStats(BaseModel):
    """Transport request statistics."""

    total_requests: int
    pending: int
    approved: int
    assigned: int
    in_progress: int
    completed: int
    cancelled: int
    by_urgency: dict[str, int]
    by_reason: dict[str, int]


# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

_transport_requests: dict[str, dict] = {}


def _reset_store() -> None:
    """Reset the in-memory store (for testing)."""
    _transport_requests.clear()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", response_model=TransportRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_transport_request(request: TransportRequestCreate) -> TransportRequestResponse:
    """Create a new transport request."""
    now = datetime.now(UTC).isoformat()
    request_id = str(uuid4())

    record = {
        "id": request_id,
        "reason": request.reason,
        "urgency": request.urgency,
        "status": RequestStatus.PENDING,
        "pickup": request.pickup.model_dump(),
        "delivery": request.delivery.model_dump(),
        "animals": [a.model_dump() for a in request.animals],
        "preferred_date": request.preferred_date,
        "preferred_time": request.preferred_time,
        "notes": request.notes,
        "requester_name": request.requester_name,
        "requester_phone": request.requester_phone,
        "requester_email": request.requester_email,
        "assigned_driver": None,
        "created_at": now,
        "updated_at": now,
    }
    _transport_requests[request_id] = record

    logger.info(
        "Transport request created", extra={"request_id": request_id, "reason": request.reason}
    )

    return TransportRequestResponse(
        id=request_id,
        reason=request.reason,
        reason_label=REASON_LABELS_ES.get(request.reason, request.reason),
        urgency=request.urgency,
        urgency_label=URGENCY_LABELS_ES.get(request.urgency, request.urgency),
        status=RequestStatus.PENDING,
        status_label=STATUS_LABELS_ES["pending"],
        pickup=request.pickup,
        delivery=request.delivery,
        animals=request.animals,
        animal_count=len(request.animals),
        preferred_date=request.preferred_date,
        preferred_time=request.preferred_time,
        notes=request.notes,
        requester_name=request.requester_name,
        requester_phone=request.requester_phone,
        requester_email=request.requester_email,
        created_at=now,
        updated_at=now,
    )


@router.get("", response_model=TransportRequestList)
async def list_transport_requests(
    status_filter: RequestStatus | None = Query(default=None, alias="status"),
    urgency: RequestUrgency | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> TransportRequestList:
    """List transport requests with filtering and pagination."""
    filtered = list(_transport_requests.values())

    if status_filter is not None:
        filtered = [r for r in filtered if r["status"] == status_filter]
    if urgency is not None:
        filtered = [r for r in filtered if r["urgency"] == urgency]

    # Sort by creation date descending
    filtered.sort(key=lambda r: r["created_at"], reverse=True)

    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = filtered[start:end]

    return TransportRequestList(
        requests=[
            TransportRequestResponse(
                id=r["id"],
                reason=r["reason"],
                reason_label=REASON_LABELS_ES.get(r["reason"], r["reason"]),
                urgency=r["urgency"],
                urgency_label=URGENCY_LABELS_ES.get(r["urgency"], r["urgency"]),
                status=r["status"],
                status_label=STATUS_LABELS_ES.get(r["status"], r["status"]),
                pickup=LocationInfo(**r["pickup"]),
                delivery=LocationInfo(**r["delivery"]),
                animals=[AnimalInfo(**a) for a in r["animals"]],
                animal_count=len(r["animals"]),
                preferred_date=r.get("preferred_date"),
                preferred_time=r.get("preferred_time"),
                notes=r.get("notes"),
                requester_name=r["requester_name"],
                requester_phone=r["requester_phone"],
                requester_email=r.get("requester_email"),
                assigned_driver=r.get("assigned_driver"),
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )
            for r in page_items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/stats", response_model=RequestStats)
async def get_request_stats() -> RequestStats:
    """Get transport request statistics."""
    all_reqs = list(_transport_requests.values())
    by_status = {}
    for s in RequestStatus:
        by_status[s.value] = sum(1 for r in all_reqs if r["status"] == s.value)

    by_urgency = {}
    for u in RequestUrgency:
        by_urgency[u.value] = sum(1 for r in all_reqs if r["urgency"] == u.value)

    by_reason = {}
    for reason in TransportReason:
        count = sum(1 for r in all_reqs if r["reason"] == reason.value)
        if count > 0:
            by_reason[reason.value] = count

    return RequestStats(
        total_requests=len(all_reqs),
        pending=by_status.get("pending", 0),
        approved=by_status.get("approved", 0),
        assigned=by_status.get("assigned", 0),
        in_progress=by_status.get("in_progress", 0),
        completed=by_status.get("completed", 0),
        cancelled=by_status.get("cancelled", 0),
        by_urgency=by_urgency,
        by_reason=by_reason,
    )


@router.get("/{request_id}", response_model=TransportRequestResponse)
async def get_transport_request(request_id: str) -> TransportRequestResponse:
    """Get a transport request by ID."""
    record = _transport_requests.get(request_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transport request '{request_id}' not found",
        )

    return TransportRequestResponse(
        id=record["id"],
        reason=record["reason"],
        reason_label=REASON_LABELS_ES.get(record["reason"], record["reason"]),
        urgency=record["urgency"],
        urgency_label=URGENCY_LABELS_ES.get(record["urgency"], record["urgency"]),
        status=record["status"],
        status_label=STATUS_LABELS_ES.get(record["status"], record["status"]),
        pickup=LocationInfo(**record["pickup"]),
        delivery=LocationInfo(**record["delivery"]),
        animals=[AnimalInfo(**a) for a in record["animals"]],
        animal_count=len(record["animals"]),
        preferred_date=record.get("preferred_date"),
        preferred_time=record.get("preferred_time"),
        notes=record.get("notes"),
        requester_name=record["requester_name"],
        requester_phone=record["requester_phone"],
        requester_email=record.get("requester_email"),
        assigned_driver=record.get("assigned_driver"),
        created_at=record["created_at"],
        updated_at=record["updated_at"],
    )


@router.put("/{request_id}/status", response_model=TransportRequestResponse)
async def update_request_status(
    request_id: str,
    update: StatusUpdateRequest,
) -> TransportRequestResponse:
    """Update transport request status with transition validation."""
    record = _transport_requests.get(request_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transport request '{request_id}' not found",
        )

    current_status = record["status"]
    valid_next = VALID_STATUS_TRANSITIONS.get(current_status, [])
    if update.new_status not in valid_next:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from '{current_status}' to '{update.new_status}'. Valid: {valid_next}",
        )

    record["status"] = update.new_status
    record["updated_at"] = datetime.now(UTC).isoformat()

    return await get_transport_request(request_id)


@router.post("/{request_id}/cancel", response_model=TransportRequestResponse)
async def cancel_request(request_id: str) -> TransportRequestResponse:
    """Cancel a transport request."""
    record = _transport_requests.get(request_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transport request '{request_id}' not found",
        )

    if record["status"] in ("completed", "cancelled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel request in '{record['status']}' status",
        )

    record["status"] = RequestStatus.CANCELLED
    record["updated_at"] = datetime.now(UTC).isoformat()

    return await get_transport_request(request_id)
