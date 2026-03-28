"""Community feature request board API.

Allows users to submit, vote on, and view feature requests
for the shelter platform.
"""

from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/feature-requests", tags=["feature-requests"])


# ---------------------------------------------------------------------------
# Constants & enums
# ---------------------------------------------------------------------------

MAX_TITLE_LENGTH: int = 120
MAX_DESCRIPTION_LENGTH: int = 1000
PAGE_SIZE_DEFAULT: int = 20
PAGE_SIZE_MAX: int = 50


class RequestStatus(enum.StrEnum):
    """Feature request lifecycle status."""

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DECLINED = "declined"


class RequestCategory(enum.StrEnum):
    """Feature request category."""

    ADOPTION = "adopcion"
    DONATIONS = "donaciones"
    VOLUNTEERING = "voluntariado"
    ANIMALS = "animales"
    WEBSITE = "sitio_web"
    EVENTS = "eventos"
    OTHER = "otro"


CATEGORY_LABELS_ES: dict[str, str] = {
    "adopcion": "Adopcion",
    "donaciones": "Donaciones",
    "voluntariado": "Voluntariado",
    "animales": "Animales",
    "sitio_web": "Sitio Web",
    "eventos": "Eventos",
    "otro": "Otro",
}

STATUS_LABELS_ES: dict[str, str] = {
    "open": "Abierto",
    "under_review": "En revision",
    "planned": "Planificado",
    "in_progress": "En progreso",
    "completed": "Completado",
    "declined": "Rechazado",
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class FeatureRequestCreate(BaseModel):
    """Create a new feature request."""

    title: str = Field(min_length=5, max_length=MAX_TITLE_LENGTH)
    description: str = Field(min_length=10, max_length=MAX_DESCRIPTION_LENGTH)
    category: RequestCategory
    submitted_by_name: str = Field(min_length=1, max_length=100)
    submitted_by_email: str = Field(min_length=5, max_length=200)


class FeatureRequestResponse(BaseModel):
    """Feature request in API responses."""

    id: int
    title: str
    description: str
    category: str
    category_label: str
    status: str
    status_label: str
    votes: int
    submitted_by_name: str
    created_at: str
    updated_at: str


class FeatureRequestListResponse(BaseModel):
    """Paginated list of feature requests."""

    items: list[FeatureRequestResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class VoteResponse(BaseModel):
    """Vote operation result."""

    request_id: int
    votes: int
    message: str


# ---------------------------------------------------------------------------
# In-memory store (MVP)
# ---------------------------------------------------------------------------

_requests: dict[int, dict[str, Any]] = {}
_next_id: int = 1
_votes: dict[str, set[int]] = {}  # voter_key -> set of request IDs


def _reset_store() -> None:
    """Reset store for testing."""
    global _next_id
    _requests.clear()
    _next_id = 1
    _votes.clear()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=FeatureRequestResponse,
    status_code=201,
    summary="Submit a feature request",
)
async def create_feature_request(
    body: FeatureRequestCreate,
) -> FeatureRequestResponse:
    """Submit a new feature request."""
    global _next_id
    now = datetime.now(UTC).isoformat()
    request_id = _next_id
    _next_id += 1

    record: dict[str, Any] = {
        "id": request_id,
        "title": body.title.strip(),
        "description": body.description.strip(),
        "category": body.category.value,
        "status": RequestStatus.OPEN.value,
        "votes": 0,
        "submitted_by_name": body.submitted_by_name.strip(),
        "submitted_by_email": body.submitted_by_email.strip(),
        "created_at": now,
        "updated_at": now,
    }
    _requests[request_id] = record

    return FeatureRequestResponse(
        **{k: v for k, v in record.items() if k != "submitted_by_email"},
        category_label=CATEGORY_LABELS_ES.get(record["category"], record["category"]),
        status_label=STATUS_LABELS_ES.get(record["status"], record["status"]),
    )


@router.get(
    "",
    response_model=FeatureRequestListResponse,
    summary="List feature requests",
)
async def list_feature_requests(
    category: RequestCategory | None = Query(None, description="Filter by category"),
    status: RequestStatus | None = Query(None, description="Filter by status"),
    sort_by: str = Query("votes", description="Sort by: votes, newest, oldest"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(PAGE_SIZE_DEFAULT, ge=1, le=PAGE_SIZE_MAX, description="Items per page"),
) -> FeatureRequestListResponse:
    """List feature requests with filtering and sorting."""
    items = list(_requests.values())

    if category:
        items = [r for r in items if r["category"] == category.value]
    if status:
        items = [r for r in items if r["status"] == status.value]

    if sort_by == "votes":
        items.sort(key=lambda r: r["votes"], reverse=True)
    elif sort_by == "newest":
        items.sort(key=lambda r: r["created_at"], reverse=True)
    elif sort_by == "oldest":
        items.sort(key=lambda r: r["created_at"])

    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]

    return FeatureRequestListResponse(
        items=[
            FeatureRequestResponse(
                **{k: v for k, v in r.items() if k != "submitted_by_email"},
                category_label=CATEGORY_LABELS_ES.get(r["category"], r["category"]),
                status_label=STATUS_LABELS_ES.get(r["status"], r["status"]),
            )
            for r in page_items
        ],
        total=total,
        page=page,
        page_size=page_size,
        has_more=end < total,
    )


@router.get(
    "/{request_id}",
    response_model=FeatureRequestResponse,
    summary="Get a single feature request",
)
async def get_feature_request(
    request_id: int = Path(ge=1, description="Feature request ID"),
) -> FeatureRequestResponse:
    """Get a single feature request by ID."""
    record = _requests.get(request_id)
    if not record:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    return FeatureRequestResponse(
        **{k: v for k, v in record.items() if k != "submitted_by_email"},
        category_label=CATEGORY_LABELS_ES.get(record["category"], record["category"]),
        status_label=STATUS_LABELS_ES.get(record["status"], record["status"]),
    )


@router.post(
    "/{request_id}/vote",
    response_model=VoteResponse,
    summary="Vote for a feature request",
)
async def vote_for_request(
    request_id: int = Path(ge=1, description="Feature request ID"),
    voter_key: str = Query("anonymous", description="Voter identifier"),
) -> VoteResponse:
    """Upvote a feature request. Each voter can vote once per request."""
    record = _requests.get(request_id)
    if not record:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    if voter_key not in _votes:
        _votes[voter_key] = set()

    if request_id in _votes[voter_key]:
        raise HTTPException(status_code=409, detail="Ya votaste por esta solicitud")

    _votes[voter_key].add(request_id)
    record["votes"] += 1

    return VoteResponse(
        request_id=request_id,
        votes=record["votes"],
        message="Voto registrado",
    )


@router.get(
    "/categories/list",
    response_model=list[dict[str, str]],
    summary="List available categories",
)
async def list_categories() -> list[dict[str, str]]:
    """Return available feature request categories with labels."""
    return [
        {"value": cat.value, "label": CATEGORY_LABELS_ES.get(cat.value, cat.value)}
        for cat in RequestCategory
    ]
