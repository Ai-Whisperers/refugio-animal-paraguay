"""Community needs board API.

Allows rescuers to post urgent needs (food, transport, supplies, medical)
and community members to respond. Supports urgency-based prioritization,
filtering by type/location, and status management.

Endpoints:
    GET  /api/community/needs               -- list all open needs (public)
    GET  /api/community/needs/{need_id}     -- get need details (public)
    POST /api/portal/rescuer/needs          -- create a new need
    PUT  /api/portal/rescuer/needs/{need_id} -- update need status
    GET  /api/portal/rescuer/needs          -- list rescuer's own needs
    POST /api/community/needs/{need_id}/respond -- respond to a need
"""

import logging
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Two routers: public community + rescuer portal
public_router = APIRouter(
    prefix="/api/community/needs",
    tags=["community-needs"],
)

rescuer_router = APIRouter(
    prefix="/api/portal/rescuer/needs",
    tags=["rescuer-needs"],
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_NEEDS_PER_PAGE = 50
DEFAULT_PAGE_SIZE = 20
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 2000


class NeedType(StrEnum):
    """Types of community needs."""

    FOOD = "food"
    TRANSPORT = "transport"
    FOSTER = "foster"
    MEDICAL = "medical"
    SUPPLIES = "supplies"
    OTHER = "other"


class UrgencyLevel(StrEnum):
    """Urgency levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class NeedStatus(StrEnum):
    """Need status."""

    OPEN = "open"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"


class ContactMethod(StrEnum):
    """Preferred contact methods."""

    EMAIL = "email"
    WHATSAPP = "whatsapp"
    PHONE = "phone"


NEED_TYPE_LABELS_ES: dict[str, str] = {
    "food": "Alimento",
    "transport": "Transporte",
    "foster": "Acogida temporal",
    "medical": "Medico",
    "supplies": "Suministros",
    "other": "Otro",
}

URGENCY_LABELS_ES: dict[str, str] = {
    "critical": "Critico",
    "high": "Alta",
    "medium": "Media",
    "low": "Baja",
}

STATUS_LABELS_ES: dict[str, str] = {
    "open": "Abierto",
    "fulfilled": "Cumplido",
    "cancelled": "Cancelado",
}

URGENCY_ORDER = {
    UrgencyLevel.CRITICAL: 0,
    UrgencyLevel.HIGH: 1,
    UrgencyLevel.MEDIUM: 2,
    UrgencyLevel.LOW: 3,
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class NeedCreateRequest(BaseModel):
    """Request to create a community need."""

    title: str = Field(max_length=MAX_TITLE_LENGTH)
    description: str = Field(max_length=MAX_DESCRIPTION_LENGTH)
    need_type: NeedType
    urgency: UrgencyLevel = UrgencyLevel.MEDIUM
    location: str = Field(max_length=200)
    contact_method: ContactMethod = ContactMethod.WHATSAPP
    contact_info: str = Field(max_length=200)
    target_date: str | None = None
    estimated_cost_pyg: int | None = None


class NeedResponse(BaseModel):
    """Community need response."""

    id: str
    rescuer_id: str
    rescuer_name: str
    title: str
    description: str
    need_type: NeedType
    need_type_label: str
    urgency: UrgencyLevel
    urgency_label: str
    location: str
    contact_method: ContactMethod
    contact_info: str
    target_date: str | None
    estimated_cost_pyg: int | None
    status: NeedStatus
    status_label: str
    responses_count: int
    created_at: str
    updated_at: str


class NeedListResponse(BaseModel):
    """Paginated list of needs."""

    needs: list[NeedResponse]
    total: int
    page: int
    page_size: int


class NeedStatusUpdate(BaseModel):
    """Update need status."""

    status: NeedStatus


class CommunityResponse(BaseModel):
    """A response to a community need."""

    id: str
    need_id: str
    responder_name: str
    message: str
    contact_info: str
    created_at: str


class RespondRequest(BaseModel):
    """Request to respond to a need."""

    responder_name: str = Field(max_length=100)
    message: str = Field(max_length=500)
    contact_info: str = Field(max_length=200)


class RespondResult(BaseModel):
    """Result of responding to a need."""

    response_id: str
    need_id: str
    message: str


# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

_needs: dict[str, dict[str, Any]] = {}
_responses: dict[str, list[dict[str, Any]]] = {}

SAMPLE_RESCUER_ID = "rescuer-001"
SAMPLE_RESCUER_NAME = "Ana Lopez"


def _reset_store() -> None:
    """Reset in-memory store (for testing)."""
    _needs.clear()
    _responses.clear()


def _build_need_response(data: dict[str, Any]) -> NeedResponse:
    """Build NeedResponse from stored data."""
    need_id = data["id"]
    return NeedResponse(
        id=need_id,
        rescuer_id=data["rescuer_id"],
        rescuer_name=data["rescuer_name"],
        title=data["title"],
        description=data["description"],
        need_type=data["need_type"],
        need_type_label=NEED_TYPE_LABELS_ES.get(data["need_type"], data["need_type"]),
        urgency=data["urgency"],
        urgency_label=URGENCY_LABELS_ES.get(data["urgency"], data["urgency"]),
        location=data["location"],
        contact_method=data["contact_method"],
        contact_info=data["contact_info"],
        target_date=data.get("target_date"),
        estimated_cost_pyg=data.get("estimated_cost_pyg"),
        status=data["status"],
        status_label=STATUS_LABELS_ES.get(data["status"], data["status"]),
        responses_count=len(_responses.get(need_id, [])),
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


def _sort_needs(needs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort needs by urgency (critical first) then by created_at DESC."""
    return sorted(
        needs,
        key=lambda n: (URGENCY_ORDER.get(n["urgency"], 99), n["created_at"]),
    )


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------


@public_router.get("", response_model=NeedListResponse)
async def list_community_needs(
    need_type: NeedType | None = Query(None, alias="type"),
    urgency: UrgencyLevel | None = None,
    location: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_NEEDS_PER_PAGE),
) -> NeedListResponse:
    """List all open community needs (public)."""
    all_needs = [n for n in _needs.values() if n["status"] == NeedStatus.OPEN]

    if need_type:
        all_needs = [n for n in all_needs if n["need_type"] == need_type]
    if urgency:
        all_needs = [n for n in all_needs if n["urgency"] == urgency]
    if location:
        all_needs = [n for n in all_needs if location.lower() in n["location"].lower()]

    sorted_needs = _sort_needs(all_needs)
    total = len(sorted_needs)
    start = (page - 1) * page_size
    page_needs = sorted_needs[start : start + page_size]

    return NeedListResponse(
        needs=[_build_need_response(n) for n in page_needs],
        total=total,
        page=page,
        page_size=page_size,
    )


@public_router.get("/{need_id}", response_model=NeedResponse)
async def get_community_need(need_id: str) -> NeedResponse:
    """Get need details (public)."""
    data = _needs.get(need_id)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Need '{need_id}' not found",
        )
    return _build_need_response(data)


@public_router.post(
    "/{need_id}/respond",
    response_model=RespondResult,
    status_code=status.HTTP_201_CREATED,
)
async def respond_to_need(need_id: str, request: RespondRequest) -> RespondResult:
    """Respond to a community need."""
    data = _needs.get(need_id)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Need '{need_id}' not found",
        )

    if data["status"] != NeedStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot respond to a closed need",
        )

    response_id = str(uuid4())
    response_data = {
        "id": response_id,
        "need_id": need_id,
        "responder_name": request.responder_name,
        "message": request.message,
        "contact_info": request.contact_info,
        "created_at": datetime.now(UTC).isoformat(),
    }

    if need_id not in _responses:
        _responses[need_id] = []
    _responses[need_id].append(response_data)

    logger.info("Need response added", extra={"need_id": need_id, "response_id": response_id})

    return RespondResult(
        response_id=response_id,
        need_id=need_id,
        message="Respuesta enviada exitosamente",
    )


# ---------------------------------------------------------------------------
# Rescuer portal endpoints
# ---------------------------------------------------------------------------


@rescuer_router.post("", response_model=NeedResponse, status_code=status.HTTP_201_CREATED)
async def create_need(request: NeedCreateRequest) -> NeedResponse:
    """Create a new community need."""
    need_id = str(uuid4())
    now = datetime.now(UTC).isoformat()

    data: dict[str, Any] = {
        "id": need_id,
        "rescuer_id": SAMPLE_RESCUER_ID,
        "rescuer_name": SAMPLE_RESCUER_NAME,
        "title": request.title,
        "description": request.description,
        "need_type": request.need_type,
        "urgency": request.urgency,
        "location": request.location,
        "contact_method": request.contact_method,
        "contact_info": request.contact_info,
        "target_date": request.target_date,
        "estimated_cost_pyg": request.estimated_cost_pyg,
        "status": NeedStatus.OPEN,
        "created_at": now,
        "updated_at": now,
    }
    _needs[need_id] = data

    logger.info("Need created", extra={"need_id": need_id, "type": request.need_type})

    return _build_need_response(data)


@rescuer_router.get("", response_model=NeedListResponse)
async def list_rescuer_needs(
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_NEEDS_PER_PAGE),
) -> NeedListResponse:
    """List rescuer's own needs."""
    my_needs = [n for n in _needs.values() if n["rescuer_id"] == SAMPLE_RESCUER_ID]
    sorted_needs = _sort_needs(my_needs)
    total = len(sorted_needs)
    start = (page - 1) * page_size
    page_needs = sorted_needs[start : start + page_size]

    return NeedListResponse(
        needs=[_build_need_response(n) for n in page_needs],
        total=total,
        page=page,
        page_size=page_size,
    )


@rescuer_router.put("/{need_id}", response_model=NeedResponse)
async def update_need_status(need_id: str, request: NeedStatusUpdate) -> NeedResponse:
    """Update need status (open/fulfilled/cancelled)."""
    data = _needs.get(need_id)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Need '{need_id}' not found",
        )

    if data["rescuer_id"] != SAMPLE_RESCUER_ID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the need creator can update status",
        )

    data["status"] = request.status
    data["updated_at"] = datetime.now(UTC).isoformat()

    logger.info(
        "Need status updated",
        extra={"need_id": need_id, "status": request.status},
    )

    return _build_need_response(data)
