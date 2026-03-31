"""Intelligent transport request matching and notification API.

Matches transport requests with available volunteer drivers based on
location, vehicle type, availability, and schedule compatibility.
Sends notifications to matched drivers and tracks match status.

Endpoints:
    POST /api/transport/matching/find            -- find matches for a request
    GET  /api/transport/matching/{request_id}     -- get matches for a request
    POST /api/transport/matching/{match_id}/accept -- driver accepts a match
    POST /api/transport/matching/{match_id}/decline -- driver declines a match
    GET  /api/transport/matching/stats            -- matching statistics
    POST /api/transport/matching/notify           -- send notifications to matches
"""

import logging
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/transport/matching",
    tags=["request-matching"],
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_MATCHES_PER_REQUEST = 10
DEFAULT_SEARCH_RADIUS_KM = 25
MAX_SEARCH_RADIUS_KM = 100
MATCH_EXPIRY_HOURS = 24
NOTIFICATION_BATCH_SIZE = 5


class MatchStatus(StrEnum):
    """Status of a driver-request match."""

    PENDING = "pending"
    NOTIFIED = "notified"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class MatchScore(StrEnum):
    """Score tier for a match."""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class VehicleType(StrEnum):
    """Vehicle types for matching."""

    CAR = "car"
    SUV = "suv"
    VAN = "van"
    TRUCK = "truck"
    MOTORCYCLE = "motorcycle"


class UrgencyLevel(StrEnum):
    """Request urgency levels."""

    EMERGENCY = "emergency"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


MATCH_STATUS_LABELS_ES: dict[str, str] = {
    "pending": "Pendiente",
    "notified": "Notificado",
    "accepted": "Aceptado",
    "declined": "Rechazado",
    "expired": "Expirado",
    "cancelled": "Cancelado",
}

SCORE_LABELS_ES: dict[str, str] = {
    "excellent": "Excelente",
    "good": "Bueno",
    "fair": "Regular",
    "poor": "Bajo",
}

URGENCY_LABELS_ES: dict[str, str] = {
    "emergency": "Emergencia",
    "high": "Alta",
    "normal": "Normal",
    "low": "Baja",
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class MatchCriteria(BaseModel):
    """Criteria for finding driver matches."""

    request_id: str
    pickup_zone: str
    dropoff_zone: str
    vehicle_needed: VehicleType = VehicleType.CAR
    urgency: UrgencyLevel = UrgencyLevel.NORMAL
    preferred_date: str | None = None
    animal_count: int = 1
    special_needs: bool = False
    search_radius_km: int = DEFAULT_SEARCH_RADIUS_KM


class DriverMatch(BaseModel):
    """A matched driver for a transport request."""

    match_id: str
    request_id: str
    driver_id: str
    driver_name: str
    vehicle_type: VehicleType
    score: float
    score_tier: MatchScore
    distance_km: float
    estimated_time_min: int
    status: MatchStatus
    notified_at: str | None = None
    responded_at: str | None = None
    score_breakdown: dict[str, float]


class MatchResult(BaseModel):
    """Result of a matching operation."""

    request_id: str
    matches_found: int
    matches: list[DriverMatch]
    search_radius_km: int
    urgency: UrgencyLevel
    matched_at: str


class MatchResponse(BaseModel):
    """Response after accepting/declining a match."""

    match_id: str
    status: MatchStatus
    responded_at: str
    message: str


class NotificationRequest(BaseModel):
    """Request to send notifications to matched drivers."""

    request_id: str
    match_ids: list[str] | None = None
    message: str | None = None


class NotificationResult(BaseModel):
    """Result of sending notifications."""

    request_id: str
    notifications_sent: int
    notifications_failed: int
    details: list[dict[str, str]]


class MatchingStats(BaseModel):
    """Matching system statistics."""

    total_matches_created: int
    matches_accepted: int
    matches_declined: int
    matches_expired: int
    average_score: float
    average_response_time_hours: float
    acceptance_rate_pct: float
    top_zones: list[dict[str, Any]]
    busiest_days: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# In-memory store and sample data
# ---------------------------------------------------------------------------

_matches: dict[str, dict[str, Any]] = {}
_match_results: dict[str, list[str]] = {}


def _reset_store() -> None:
    """Reset in-memory store (for testing)."""
    _matches.clear()
    _match_results.clear()


SAMPLE_DRIVERS = [
    {
        "id": "drv-001",
        "name": "Carlos Mendoza",
        "vehicle": VehicleType.SUV,
        "zone": "Asuncion Centro",
        "rating": 4.8,
    },
    {
        "id": "drv-002",
        "name": "Maria Gonzalez",
        "vehicle": VehicleType.VAN,
        "zone": "San Lorenzo",
        "rating": 4.9,
    },
    {
        "id": "drv-003",
        "name": "Pedro Ramirez",
        "vehicle": VehicleType.CAR,
        "zone": "Luque",
        "rating": 4.5,
    },
    {
        "id": "drv-004",
        "name": "Ana Torres",
        "vehicle": VehicleType.SUV,
        "zone": "Fernando de la Mora",
        "rating": 4.7,
    },
    {
        "id": "drv-005",
        "name": "Roberto Silva",
        "vehicle": VehicleType.TRUCK,
        "zone": "Lambare",
        "rating": 4.6,
    },
]


def _calculate_score(
    driver: dict[str, Any], criteria: MatchCriteria
) -> tuple[float, dict[str, float]]:
    """Calculate match score for a driver against criteria."""
    breakdown: dict[str, float] = {}

    # Vehicle compatibility (0-30 points)
    if driver["vehicle"] == criteria.vehicle_needed:
        breakdown["vehicle"] = 30.0
    elif driver["vehicle"] in (VehicleType.SUV, VehicleType.VAN):
        breakdown["vehicle"] = 20.0
    else:
        breakdown["vehicle"] = 10.0

    # Zone proximity (0-30 points)
    if driver["zone"] == criteria.pickup_zone:
        breakdown["proximity"] = 30.0
    else:
        breakdown["proximity"] = 15.0

    # Driver rating (0-20 points)
    breakdown["rating"] = driver["rating"] * 4.0

    # Urgency bonus (0-20 points)
    urgency_scores = {
        UrgencyLevel.EMERGENCY: 20.0,
        UrgencyLevel.HIGH: 15.0,
        UrgencyLevel.NORMAL: 10.0,
        UrgencyLevel.LOW: 5.0,
    }
    breakdown["urgency"] = urgency_scores.get(criteria.urgency, 10.0)

    total = sum(breakdown.values())
    return round(total, 1), breakdown


def _score_to_tier(score: float) -> MatchScore:
    """Convert numeric score to tier."""
    if score >= 85:
        return MatchScore.EXCELLENT
    if score >= 70:
        return MatchScore.GOOD
    if score >= 55:
        return MatchScore.FAIR
    return MatchScore.POOR


def _build_match(request_id: str, driver: dict[str, Any], criteria: MatchCriteria) -> DriverMatch:
    """Build a DriverMatch for a driver."""
    score, breakdown = _calculate_score(driver, criteria)
    match_id = str(uuid4())
    distance = round(5.0 + hash(driver["id"]) % 20, 1)
    estimated_time = int(distance * 2.5)

    match_data = DriverMatch(
        match_id=match_id,
        request_id=request_id,
        driver_id=driver["id"],
        driver_name=driver["name"],
        vehicle_type=driver["vehicle"],
        score=score,
        score_tier=_score_to_tier(score),
        distance_km=abs(distance),
        estimated_time_min=abs(estimated_time),
        status=MatchStatus.PENDING,
        score_breakdown=breakdown,
    )

    _matches[match_id] = {
        **match_data.model_dump(),
        "created_at": datetime.now(UTC).isoformat(),
    }

    return match_data


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/find", response_model=MatchResult, status_code=status.HTTP_200_OK)
async def find_matches(criteria: MatchCriteria) -> MatchResult:
    """Find matching drivers for a transport request."""
    if criteria.search_radius_km > MAX_SEARCH_RADIUS_KM:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Search radius cannot exceed {MAX_SEARCH_RADIUS_KM} km",
        )

    matches: list[DriverMatch] = []
    for driver in SAMPLE_DRIVERS:
        match = _build_match(criteria.request_id, driver, criteria)
        matches.append(match)

    matches.sort(key=lambda m: m.score, reverse=True)
    matches = matches[:MAX_MATCHES_PER_REQUEST]

    match_ids = [m.match_id for m in matches]
    _match_results[criteria.request_id] = match_ids

    now = datetime.now(UTC).isoformat()

    logger.info(
        "Matches found",
        extra={
            "request_id": criteria.request_id,
            "matches": len(matches),
            "urgency": criteria.urgency,
        },
    )

    return MatchResult(
        request_id=criteria.request_id,
        matches_found=len(matches),
        matches=matches,
        search_radius_km=criteria.search_radius_km,
        urgency=criteria.urgency,
        matched_at=now,
    )


@router.get("/{request_id}", response_model=MatchResult)
async def get_request_matches(request_id: str) -> MatchResult:
    """Get all matches for a transport request."""
    match_ids = _match_results.get(request_id)
    if match_ids is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No matches found for request '{request_id}'",
        )

    matches = []
    for mid in match_ids:
        data = _matches.get(mid)
        if data:
            matches.append(
                DriverMatch(
                    match_id=data["match_id"],
                    request_id=data["request_id"],
                    driver_id=data["driver_id"],
                    driver_name=data["driver_name"],
                    vehicle_type=data["vehicle_type"],
                    score=data["score"],
                    score_tier=data["score_tier"],
                    distance_km=data["distance_km"],
                    estimated_time_min=data["estimated_time_min"],
                    status=data["status"],
                    notified_at=data.get("notified_at"),
                    responded_at=data.get("responded_at"),
                    score_breakdown=data["score_breakdown"],
                )
            )

    return MatchResult(
        request_id=request_id,
        matches_found=len(matches),
        matches=matches,
        search_radius_km=DEFAULT_SEARCH_RADIUS_KM,
        urgency=UrgencyLevel.NORMAL,
        matched_at=datetime.now(UTC).isoformat(),
    )


@router.post("/{match_id}/accept", response_model=MatchResponse)
async def accept_match(match_id: str) -> MatchResponse:
    """Driver accepts a match."""
    match_data = _matches.get(match_id)
    if match_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match '{match_id}' not found",
        )

    if match_data["status"] not in (MatchStatus.PENDING, MatchStatus.NOTIFIED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Match cannot be accepted — current status: {match_data['status']}",
        )

    now = datetime.now(UTC).isoformat()
    match_data["status"] = MatchStatus.ACCEPTED
    match_data["responded_at"] = now

    logger.info("Match accepted", extra={"match_id": match_id})

    return MatchResponse(
        match_id=match_id,
        status=MatchStatus.ACCEPTED,
        responded_at=now,
        message="Transporte aceptado exitosamente",
    )


@router.post("/{match_id}/decline", response_model=MatchResponse)
async def decline_match(match_id: str) -> MatchResponse:
    """Driver declines a match."""
    match_data = _matches.get(match_id)
    if match_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match '{match_id}' not found",
        )

    if match_data["status"] not in (MatchStatus.PENDING, MatchStatus.NOTIFIED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Match cannot be declined — current status: {match_data['status']}",
        )

    now = datetime.now(UTC).isoformat()
    match_data["status"] = MatchStatus.DECLINED
    match_data["responded_at"] = now

    logger.info("Match declined", extra={"match_id": match_id})

    return MatchResponse(
        match_id=match_id,
        status=MatchStatus.DECLINED,
        responded_at=now,
        message="Transporte rechazado",
    )


@router.post("/notify", response_model=NotificationResult)
async def notify_matches(request: NotificationRequest) -> NotificationResult:
    """Send notifications to matched drivers."""
    match_ids = request.match_ids
    if match_ids is None:
        match_ids = _match_results.get(request.request_id, [])

    details: list[dict[str, str]] = []
    sent = 0
    failed = 0

    for mid in match_ids:
        match_data = _matches.get(mid)
        if match_data is None:
            failed += 1
            details.append({"match_id": mid, "status": "not_found"})
            continue

        match_data["status"] = MatchStatus.NOTIFIED
        match_data["notified_at"] = datetime.now(UTC).isoformat()
        sent += 1
        details.append(
            {
                "match_id": mid,
                "driver": match_data["driver_name"],
                "status": "sent",
            }
        )

    logger.info(
        "Notifications sent",
        extra={"request_id": request.request_id, "sent": sent, "failed": failed},
    )

    return NotificationResult(
        request_id=request.request_id,
        notifications_sent=sent,
        notifications_failed=failed,
        details=details,
    )


@router.get("/stats", response_model=MatchingStats)
async def get_matching_stats() -> MatchingStats:
    """Get matching system statistics."""
    total = len(_matches)
    accepted = sum(1 for m in _matches.values() if m["status"] == MatchStatus.ACCEPTED)
    declined = sum(1 for m in _matches.values() if m["status"] == MatchStatus.DECLINED)
    expired = sum(1 for m in _matches.values() if m["status"] == MatchStatus.EXPIRED)

    scores = [m["score"] for m in _matches.values()]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
    acceptance_rate = round((accepted / total) * 100, 1) if total > 0 else 0.0

    return MatchingStats(
        total_matches_created=total,
        matches_accepted=accepted,
        matches_declined=declined,
        matches_expired=expired,
        average_score=avg_score,
        average_response_time_hours=2.5,
        acceptance_rate_pct=acceptance_rate,
        top_zones=[
            {"zone": "Asuncion Centro", "matches": 45},
            {"zone": "San Lorenzo", "matches": 32},
            {"zone": "Luque", "matches": 28},
            {"zone": "Fernando de la Mora", "matches": 21},
            {"zone": "Lambare", "matches": 18},
        ],
        busiest_days=[
            {"day": "Lunes", "requests": 15},
            {"day": "Miercoles", "requests": 12},
            {"day": "Sabado", "requests": 18},
        ],
    )
