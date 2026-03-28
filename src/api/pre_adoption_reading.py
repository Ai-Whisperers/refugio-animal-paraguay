"""Pre-adoption reading enforcement API.

Adopters must complete required educational readings before submitting
an adoption application. This module tracks reading progress and
provides verification for the adoption flow.

Endpoints:
    GET  /api/adoption-reading/requirements    -- list required readings
    POST /api/adoption-reading/complete/{id}   -- mark a reading as completed
    GET  /api/adoption-reading/progress         -- get reading progress
    GET  /api/adoption-reading/verify           -- verify all readings done
"""

import logging
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/adoption-reading", tags=["pre-adoption-reading"])

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_READINGS = 20
MIN_READING_TIME_SECONDS = 30
SESSION_EXPIRY_DAYS = 30
READING_COMPLETE_THRESHOLD = 1.0


class ReadingCategory(StrEnum):
    """Categories for required reading material."""

    RESPONSIBLE_OWNERSHIP = "responsible_ownership"
    HEALTH_CARE = "health_care"
    LEGAL_REQUIREMENTS = "legal_requirements"
    COMMITMENT = "commitment"
    PREPARATION = "preparation"


class ReadingStatus(StrEnum):
    """Status of a reading item for a user."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ReadingRequirement(BaseModel):
    """A single required reading item."""

    id: str = Field(..., description="Unique reading identifier")
    title: str = Field(..., description="Reading title in Spanish")
    description: str = Field(..., description="Brief description")
    category: ReadingCategory
    estimated_minutes: int = Field(..., ge=1, le=60)
    content_url: str = Field(..., description="URL to the educational content")
    order: int = Field(..., ge=1, description="Display order")
    required: bool = Field(default=True, description="Whether this reading is mandatory")


class ReadingProgress(BaseModel):
    """Progress tracking for a single reading."""

    reading_id: str
    status: ReadingStatus = ReadingStatus.NOT_STARTED
    started_at: datetime | None = None
    completed_at: datetime | None = None
    time_spent_seconds: int = 0


class ReadingProgressSummary(BaseModel):
    """Overall reading progress summary."""

    total_required: int
    completed: int
    completion_percentage: float
    all_required_complete: bool
    readings: list[ReadingProgress]
    session_id: str


class ReadingVerification(BaseModel):
    """Verification result for adoption eligibility."""

    eligible: bool
    completed_count: int
    required_count: int
    missing_readings: list[str]
    verified_at: datetime


class ReadingCompleteRequest(BaseModel):
    """Request to mark a reading as completed."""

    time_spent_seconds: int = Field(..., ge=0, description="Time spent reading in seconds")
    session_id: str = Field(..., min_length=1, description="Reading session identifier")


class ReadingCompleteResponse(BaseModel):
    """Response after marking a reading complete."""

    reading_id: str
    status: ReadingStatus
    completed_at: datetime
    progress_summary: ReadingProgressSummary


# ---------------------------------------------------------------------------
# Required Readings Data
# ---------------------------------------------------------------------------

REQUIRED_READINGS: list[dict[str, Any]] = [
    {
        "id": "responsible-ownership-basics",
        "title": "Tenencia responsable de mascotas",
        "description": (
            "Aprende sobre las responsabilidades fundamentales " "de tener una mascota en Paraguay."
        ),
        "category": ReadingCategory.RESPONSIBLE_OWNERSHIP,
        "estimated_minutes": 5,
        "content_url": "/educacion/articulos/tenencia-responsable",
        "order": 1,
        "required": True,
    },
    {
        "id": "health-vaccination-guide",
        "title": "Guía de vacunación y salud animal",
        "description": ("Calendario de vacunación y cuidados veterinarios esenciales."),
        "category": ReadingCategory.HEALTH_CARE,
        "estimated_minutes": 8,
        "content_url": "/educacion/articulos/calendario-vacunacion",
        "order": 2,
        "required": True,
    },
    {
        "id": "legal-requirements-py",
        "title": "Requisitos legales para adopción en Paraguay",
        "description": (
            "Marco legal y requisitos para la adopción " "responsable de animales en Paraguay."
        ),
        "category": ReadingCategory.LEGAL_REQUIREMENTS,
        "estimated_minutes": 6,
        "content_url": "/educacion/articulos/requisitos-legales",
        "order": 3,
        "required": True,
    },
    {
        "id": "long-term-commitment",
        "title": "Compromiso a largo plazo",
        "description": ("Entender el compromiso de 10-15 años " "que implica adoptar una mascota."),
        "category": ReadingCategory.COMMITMENT,
        "estimated_minutes": 4,
        "content_url": "/educacion/articulos/compromiso-adopcion",
        "order": 4,
        "required": True,
    },
    {
        "id": "home-preparation",
        "title": "Preparando tu hogar para una mascota",
        "description": ("Cómo preparar tu espacio y familia " "para recibir a un nuevo miembro."),
        "category": ReadingCategory.PREPARATION,
        "estimated_minutes": 5,
        "content_url": "/educacion/articulos/preparar-hogar",
        "order": 5,
        "required": True,
    },
]

# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

_reading_sessions: dict[str, dict[str, ReadingProgress]] = {}


def _reset_store() -> None:
    """Reset in-memory store (for testing)."""
    _reading_sessions.clear()


def _get_requirements() -> list[ReadingRequirement]:
    """Return all reading requirements."""
    return [ReadingRequirement(**r) for r in REQUIRED_READINGS]


def _get_required_ids() -> set[str]:
    """Return IDs of required readings."""
    return {r["id"] for r in REQUIRED_READINGS if r.get("required", True)}


def _get_session_progress(session_id: str) -> dict[str, ReadingProgress]:
    """Get or create progress for a session."""
    if session_id not in _reading_sessions:
        _reading_sessions[session_id] = {}
    return _reading_sessions[session_id]


def _build_progress_summary(session_id: str) -> ReadingProgressSummary:
    """Build a progress summary for a session."""
    progress = _get_session_progress(session_id)
    required_ids = _get_required_ids()
    completed_ids = {
        rid
        for rid, p in progress.items()
        if p.status == ReadingStatus.COMPLETED and rid in required_ids
    }

    all_readings = []
    for req in REQUIRED_READINGS:
        rid = req["id"]
        if rid in progress:
            all_readings.append(progress[rid])
        else:
            all_readings.append(ReadingProgress(reading_id=rid))

    total_required = len(required_ids)
    completed_count = len(completed_ids)
    pct = round(completed_count / total_required * 100, 1) if total_required > 0 else 0.0

    return ReadingProgressSummary(
        total_required=total_required,
        completed=completed_count,
        completion_percentage=pct,
        all_required_complete=completed_count >= total_required,
        readings=all_readings,
        session_id=session_id,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/requirements", response_model=list[ReadingRequirement])
async def list_reading_requirements(
    category: ReadingCategory | None = Query(None, description="Filter by category"),
) -> list[ReadingRequirement]:
    """List all required pre-adoption readings."""
    requirements = _get_requirements()
    if category is not None:
        requirements = [r for r in requirements if r.category == category]
    return requirements


@router.post(
    "/complete/{reading_id}",
    response_model=ReadingCompleteResponse,
    status_code=status.HTTP_200_OK,
)
async def complete_reading(
    reading_id: str,
    request: ReadingCompleteRequest,
) -> ReadingCompleteResponse:
    """Mark a reading as completed."""
    required_ids = {r["id"] for r in REQUIRED_READINGS}
    if reading_id not in required_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reading '{reading_id}' not found",
        )

    if request.time_spent_seconds < MIN_READING_TIME_SECONDS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Minimum reading time is {MIN_READING_TIME_SECONDS} seconds. "
                f"Please spend more time reading the material."
            ),
        )

    progress = _get_session_progress(request.session_id)
    now = datetime.now(UTC)

    existing = progress.get(reading_id)
    if existing and existing.status == ReadingStatus.COMPLETED:
        summary = _build_progress_summary(request.session_id)
        return ReadingCompleteResponse(
            reading_id=reading_id,
            status=ReadingStatus.COMPLETED,
            completed_at=existing.completed_at or now,
            progress_summary=summary,
        )

    reading_progress = ReadingProgress(
        reading_id=reading_id,
        status=ReadingStatus.COMPLETED,
        started_at=existing.started_at if existing else now,
        completed_at=now,
        time_spent_seconds=request.time_spent_seconds,
    )
    progress[reading_id] = reading_progress

    logger.info(
        "Reading completed",
        extra={
            "reading_id": reading_id,
            "session_id": request.session_id,
            "time_spent": request.time_spent_seconds,
        },
    )

    summary = _build_progress_summary(request.session_id)
    return ReadingCompleteResponse(
        reading_id=reading_id,
        status=ReadingStatus.COMPLETED,
        completed_at=now,
        progress_summary=summary,
    )


@router.get("/progress", response_model=ReadingProgressSummary)
async def get_reading_progress(
    session_id: str = Query(..., min_length=1, description="Reading session ID"),
) -> ReadingProgressSummary:
    """Get reading progress for a session."""
    return _build_progress_summary(session_id)


@router.get("/verify", response_model=ReadingVerification)
async def verify_reading_completion(
    session_id: str = Query(..., min_length=1, description="Reading session ID"),
) -> ReadingVerification:
    """Verify all required readings are completed for adoption eligibility."""
    progress = _get_session_progress(session_id)
    required_ids = _get_required_ids()
    completed_ids = {
        rid
        for rid, p in progress.items()
        if p.status == ReadingStatus.COMPLETED and rid in required_ids
    }
    missing = sorted(required_ids - completed_ids)

    return ReadingVerification(
        eligible=len(missing) == 0,
        completed_count=len(completed_ids),
        required_count=len(required_ids),
        missing_readings=missing,
        verified_at=datetime.now(UTC),
    )
