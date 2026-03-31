"""Admin moderation tools for rescuer management.

Provides moderation capabilities for managing rescuer profiles,
campaigns, content flags, and moderation history.

Endpoints:
    GET  /api/admin/moderation/rescuers           -- list rescuers with moderation info
    POST /api/admin/moderation/rescuers/{id}/verify    -- verify/unverify rescuer
    POST /api/admin/moderation/rescuers/{id}/suspend   -- suspend/unsuspend rescuer
    POST /api/admin/moderation/rescuers/{id}/flag      -- flag rescuer for review
    POST /api/admin/moderation/rescuers/bulk           -- bulk actions
    GET  /api/admin/moderation/campaigns          -- list campaigns pending moderation
    POST /api/admin/moderation/campaigns/{id}/review   -- approve/reject campaign
    GET  /api/admin/moderation/flags              -- list content flags
    POST /api/admin/moderation/flags/{id}/review       -- review a flag
    GET  /api/admin/moderation/history            -- moderation action history
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
    prefix="/api/admin/moderation",
    tags=["admin-moderation"],
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class RescuerStatus(StrEnum):
    """Rescuer account status."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"


class VerificationStatus(StrEnum):
    """Rescuer verification status."""

    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    UNDER_REVIEW = "under_review"


class ModerationAction(StrEnum):
    """Types of moderation actions."""

    VERIFY = "verify"
    UNVERIFY = "unverify"
    SUSPEND = "suspend"
    UNSUSPEND = "unsuspend"
    FLAG = "flag"
    UNFLAG = "unflag"
    APPROVE_CAMPAIGN = "approve_campaign"
    REJECT_CAMPAIGN = "reject_campaign"
    DISMISS_FLAG = "dismiss_flag"
    REMOVE_CONTENT = "remove_content"


class CampaignStatus(StrEnum):
    """Campaign moderation status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class FlagStatus(StrEnum):
    """Content flag status."""

    OPEN = "open"
    REVIEWED = "reviewed"
    DISMISSED = "dismissed"
    ACTION_TAKEN = "action_taken"


class FlagReason(StrEnum):
    """Reasons for flagging content."""

    INAPPROPRIATE = "inappropriate"
    SPAM = "spam"
    MISLEADING = "misleading"
    ABUSE = "abuse"
    OTHER = "other"


class BulkActionType(StrEnum):
    """Supported bulk actions."""

    VERIFY = "verify"
    UNVERIFY = "unverify"
    SUSPEND = "suspend"
    UNSUSPEND = "unsuspend"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class RescuerModerationInfo(BaseModel):
    """Rescuer with moderation details."""

    id: str
    name: str
    email: str
    status: RescuerStatus
    verification_status: VerificationStatus
    animal_count: int
    supporter_count: int
    flag_count: int
    registered_at: str
    last_active: str
    location: str


class RescuerListResponse(BaseModel):
    """Paginated rescuer list."""

    rescuers: list[RescuerModerationInfo]
    total: int
    page: int
    page_size: int


class VerifyRequest(BaseModel):
    """Request to verify or unverify a rescuer."""

    verify: bool = True
    reason: str = Field(min_length=1, max_length=500)


class SuspendRequest(BaseModel):
    """Request to suspend or unsuspend a rescuer."""

    suspend: bool = True
    reason: str = Field(min_length=1, max_length=500)


class FlagRequest(BaseModel):
    """Request to flag a rescuer for review."""

    reason: FlagReason
    details: str = Field(min_length=1, max_length=1000)


class BulkActionRequest(BaseModel):
    """Bulk moderation action request."""

    rescuer_ids: list[str] = Field(min_length=1)
    action: BulkActionType
    reason: str = Field(min_length=1, max_length=500)


class BulkActionResponse(BaseModel):
    """Bulk action result."""

    processed: int
    failed: int
    errors: list[str]


class CampaignModerationInfo(BaseModel):
    """Campaign pending moderation."""

    id: str
    title: str
    rescuer_id: str
    rescuer_name: str
    description: str
    goal_amount: float
    currency: str
    status: CampaignStatus
    created_at: str
    rescuer_verified: bool


class CampaignListResponse(BaseModel):
    """Paginated campaign list."""

    campaigns: list[CampaignModerationInfo]
    total: int


class CampaignReviewRequest(BaseModel):
    """Request to approve or reject a campaign."""

    approve: bool
    reason: str = Field(min_length=1, max_length=500)


class ContentFlag(BaseModel):
    """A content flag submitted by a user."""

    id: str
    content_type: str
    content_id: str
    flagged_by: str
    reason: FlagReason
    details: str
    status: FlagStatus
    created_at: str
    reviewed_at: str | None = None
    reviewed_by: str | None = None
    resolution: str | None = None


class FlagListResponse(BaseModel):
    """Paginated flag list."""

    flags: list[ContentFlag]
    total: int


class FlagReviewRequest(BaseModel):
    """Request to review a content flag."""

    action: str = Field(description="dismiss, remove_content, suspend_rescuer, contact_rescuer")
    reason: str = Field(min_length=1, max_length=500)


class ModerationLogEntry(BaseModel):
    """A single moderation action log entry."""

    id: str
    action: ModerationAction
    target_type: str
    target_id: str
    target_name: str
    admin_id: str
    reason: str
    timestamp: str


class ModerationHistoryResponse(BaseModel):
    """Paginated moderation history."""

    entries: list[ModerationLogEntry]
    total: int


class ModerationActionResponse(BaseModel):
    """Response after a moderation action."""

    success: bool
    message: str
    action: ModerationAction


# ---------------------------------------------------------------------------
# In-memory stores and sample data
# ---------------------------------------------------------------------------

SAMPLE_RESCUERS: list[dict[str, Any]] = [
    {
        "id": "resc-001",
        "name": "Carlos Mendoza",
        "email": "carlos@rescate.py",
        "status": RescuerStatus.ACTIVE,
        "verification_status": VerificationStatus.VERIFIED,
        "animal_count": 23,
        "supporter_count": 45,
        "flag_count": 0,
        "registered_at": "2025-06-15T10:00:00Z",
        "last_active": "2026-03-27T14:30:00Z",
        "location": "Asuncion",
    },
    {
        "id": "resc-002",
        "name": "Ana Benitez",
        "email": "ana@protectora.py",
        "status": RescuerStatus.ACTIVE,
        "verification_status": VerificationStatus.UNVERIFIED,
        "animal_count": 8,
        "supporter_count": 12,
        "flag_count": 2,
        "registered_at": "2026-01-10T08:00:00Z",
        "last_active": "2026-03-26T09:15:00Z",
        "location": "San Lorenzo",
    },
    {
        "id": "resc-003",
        "name": "Miguel Torres",
        "email": "miguel@fauna.py",
        "status": RescuerStatus.SUSPENDED,
        "verification_status": VerificationStatus.UNVERIFIED,
        "animal_count": 5,
        "supporter_count": 3,
        "flag_count": 4,
        "registered_at": "2025-11-20T12:00:00Z",
        "last_active": "2026-02-15T16:45:00Z",
        "location": "Luque",
    },
    {
        "id": "resc-004",
        "name": "Laura Gimenez",
        "email": "laura@refugio.py",
        "status": RescuerStatus.ACTIVE,
        "verification_status": VerificationStatus.VERIFIED,
        "animal_count": 31,
        "supporter_count": 67,
        "flag_count": 0,
        "registered_at": "2025-03-01T09:00:00Z",
        "last_active": "2026-03-28T08:00:00Z",
        "location": "Asuncion",
    },
    {
        "id": "resc-005",
        "name": "Pedro Caceres",
        "email": "pedro@animales.py",
        "status": RescuerStatus.PENDING,
        "verification_status": VerificationStatus.UNDER_REVIEW,
        "animal_count": 2,
        "supporter_count": 0,
        "flag_count": 1,
        "registered_at": "2026-03-20T14:00:00Z",
        "last_active": "2026-03-25T11:30:00Z",
        "location": "Fernando de la Mora",
    },
]

SAMPLE_CAMPAIGNS: list[dict[str, Any]] = [
    {
        "id": "camp-001",
        "title": "Esterilizacion masiva en Luque",
        "rescuer_id": "resc-002",
        "rescuer_name": "Ana Benitez",
        "description": "Campana de esterilizacion para 50 animales callejeros",
        "goal_amount": 5000000,
        "currency": "PYG",
        "status": CampaignStatus.PENDING,
        "created_at": "2026-03-25T10:00:00Z",
        "rescuer_verified": False,
    },
    {
        "id": "camp-002",
        "title": "Refugio temporal en San Lorenzo",
        "rescuer_id": "resc-004",
        "rescuer_name": "Laura Gimenez",
        "description": "Construir un refugio temporal para 20 animales rescatados",
        "goal_amount": 8000000,
        "currency": "PYG",
        "status": CampaignStatus.PENDING,
        "created_at": "2026-03-26T15:00:00Z",
        "rescuer_verified": True,
    },
    {
        "id": "camp-003",
        "title": "Alimentacion de emergencia",
        "rescuer_id": "resc-001",
        "rescuer_name": "Carlos Mendoza",
        "description": "Compra de alimento para animales rescatados de inundacion",
        "goal_amount": 2000000,
        "currency": "PYG",
        "status": CampaignStatus.APPROVED,
        "created_at": "2026-03-20T08:00:00Z",
        "rescuer_verified": True,
    },
]

SAMPLE_FLAGS: list[dict[str, Any]] = [
    {
        "id": "flag-001",
        "content_type": "profile",
        "content_id": "resc-002",
        "flagged_by": "user-101",
        "reason": FlagReason.MISLEADING,
        "details": "Fotos de animales que no estan en su cuidado",
        "status": FlagStatus.OPEN,
        "created_at": "2026-03-24T16:00:00Z",
        "reviewed_at": None,
        "reviewed_by": None,
        "resolution": None,
    },
    {
        "id": "flag-002",
        "content_type": "campaign",
        "content_id": "camp-001",
        "flagged_by": "user-205",
        "reason": FlagReason.SPAM,
        "details": "Campana duplicada con informacion incorrecta",
        "status": FlagStatus.OPEN,
        "created_at": "2026-03-25T11:00:00Z",
        "reviewed_at": None,
        "reviewed_by": None,
        "resolution": None,
    },
    {
        "id": "flag-003",
        "content_type": "post",
        "content_id": "post-045",
        "flagged_by": "user-312",
        "reason": FlagReason.INAPPROPRIATE,
        "details": "Contenido inapropiado en publicacion",
        "status": FlagStatus.REVIEWED,
        "created_at": "2026-03-22T09:00:00Z",
        "reviewed_at": "2026-03-23T10:00:00Z",
        "reviewed_by": "admin-001",
        "resolution": "Contenido removido",
    },
]

_moderation_log: list[dict[str, Any]] = []


_ORIGINAL_RESCUERS = [
    dict(r)
    for r in [
        {
            "id": "resc-001",
            "name": "Carlos Mendoza",
            "email": "carlos@rescate.py",
            "status": RescuerStatus.ACTIVE,
            "verification_status": VerificationStatus.VERIFIED,
            "animal_count": 23,
            "supporter_count": 45,
            "flag_count": 0,
            "registered_at": "2025-06-15T10:00:00Z",
            "last_active": "2026-03-27T14:30:00Z",
            "location": "Asuncion",
        },
        {
            "id": "resc-002",
            "name": "Ana Benitez",
            "email": "ana@protectora.py",
            "status": RescuerStatus.ACTIVE,
            "verification_status": VerificationStatus.UNVERIFIED,
            "animal_count": 8,
            "supporter_count": 12,
            "flag_count": 2,
            "registered_at": "2026-01-10T08:00:00Z",
            "last_active": "2026-03-26T09:15:00Z",
            "location": "San Lorenzo",
        },
        {
            "id": "resc-003",
            "name": "Miguel Torres",
            "email": "miguel@fauna.py",
            "status": RescuerStatus.SUSPENDED,
            "verification_status": VerificationStatus.UNVERIFIED,
            "animal_count": 5,
            "supporter_count": 3,
            "flag_count": 4,
            "registered_at": "2025-11-20T12:00:00Z",
            "last_active": "2026-02-15T16:45:00Z",
            "location": "Luque",
        },
        {
            "id": "resc-004",
            "name": "Laura Gimenez",
            "email": "laura@refugio.py",
            "status": RescuerStatus.ACTIVE,
            "verification_status": VerificationStatus.VERIFIED,
            "animal_count": 31,
            "supporter_count": 67,
            "flag_count": 0,
            "registered_at": "2025-03-01T09:00:00Z",
            "last_active": "2026-03-28T08:00:00Z",
            "location": "Asuncion",
        },
        {
            "id": "resc-005",
            "name": "Pedro Caceres",
            "email": "pedro@animales.py",
            "status": RescuerStatus.PENDING,
            "verification_status": VerificationStatus.UNDER_REVIEW,
            "animal_count": 2,
            "supporter_count": 0,
            "flag_count": 1,
            "registered_at": "2026-03-20T14:00:00Z",
            "last_active": "2026-03-25T11:30:00Z",
            "location": "Fernando de la Mora",
        },
    ]
]


def _reset_store() -> None:
    """Reset in-memory stores (for testing)."""
    _moderation_log.clear()
    SAMPLE_RESCUERS.clear()
    SAMPLE_RESCUERS.extend(dict(r) for r in _ORIGINAL_RESCUERS)
    for campaign in SAMPLE_CAMPAIGNS:
        if campaign["id"] == "camp-001" or campaign["id"] == "camp-002":
            campaign["status"] = CampaignStatus.PENDING
    for flag in SAMPLE_FLAGS:
        if flag["id"] in ("flag-001", "flag-002"):
            flag["status"] = FlagStatus.OPEN
            flag["reviewed_at"] = None
            flag["reviewed_by"] = None
            flag["resolution"] = None


def _log_action(
    action: ModerationAction,
    target_type: str,
    target_id: str,
    target_name: str,
    reason: str,
) -> ModerationLogEntry:
    """Record a moderation action."""
    entry = {
        "id": str(uuid4()),
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "target_name": target_name,
        "admin_id": "admin-001",
        "reason": reason,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    _moderation_log.append(entry)
    return ModerationLogEntry(**entry)


def _find_rescuer(rescuer_id: str) -> dict[str, Any]:
    """Find a rescuer by ID or raise 404."""
    for rescuer in SAMPLE_RESCUERS:
        if rescuer["id"] == rescuer_id:
            return rescuer
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Rescuer '{rescuer_id}' not found",
    )


# ---------------------------------------------------------------------------
# Endpoints — Rescuers
# ---------------------------------------------------------------------------


@router.get("/rescuers", response_model=RescuerListResponse)
async def list_rescuers(
    search: str | None = None,
    status_filter: RescuerStatus | None = Query(None, alias="status"),
    verification: VerificationStatus | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
) -> RescuerListResponse:
    """List rescuers with moderation information."""
    filtered = list(SAMPLE_RESCUERS)

    if search:
        term = search.lower()
        filtered = [r for r in filtered if term in r["name"].lower() or term in r["email"].lower()]

    if status_filter:
        filtered = [r for r in filtered if r["status"] == status_filter]

    if verification:
        filtered = [r for r in filtered if r["verification_status"] == verification]

    total = len(filtered)
    start = (page - 1) * page_size
    page_items = filtered[start : start + page_size]

    return RescuerListResponse(
        rescuers=[RescuerModerationInfo(**r) for r in page_items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/rescuers/{rescuer_id}/verify", response_model=ModerationActionResponse)
async def verify_rescuer(rescuer_id: str, request: VerifyRequest) -> ModerationActionResponse:
    """Verify or unverify a rescuer."""
    rescuer = _find_rescuer(rescuer_id)

    if request.verify:
        rescuer["verification_status"] = VerificationStatus.VERIFIED
        action = ModerationAction.VERIFY
        message = f"Rescuer '{rescuer['name']}' verified"
    else:
        rescuer["verification_status"] = VerificationStatus.UNVERIFIED
        action = ModerationAction.UNVERIFY
        message = f"Rescuer '{rescuer['name']}' unverified"

    _log_action(action, "rescuer", rescuer_id, rescuer["name"], request.reason)
    logger.info(message, extra={"rescuer_id": rescuer_id, "action": action})

    return ModerationActionResponse(success=True, message=message, action=action)


@router.post("/rescuers/{rescuer_id}/suspend", response_model=ModerationActionResponse)
async def suspend_rescuer(rescuer_id: str, request: SuspendRequest) -> ModerationActionResponse:
    """Suspend or unsuspend a rescuer."""
    rescuer = _find_rescuer(rescuer_id)

    if request.suspend:
        rescuer["status"] = RescuerStatus.SUSPENDED
        action = ModerationAction.SUSPEND
        message = f"Rescuer '{rescuer['name']}' suspended"
    else:
        rescuer["status"] = RescuerStatus.ACTIVE
        action = ModerationAction.UNSUSPEND
        message = f"Rescuer '{rescuer['name']}' unsuspended"

    _log_action(action, "rescuer", rescuer_id, rescuer["name"], request.reason)
    logger.info(message, extra={"rescuer_id": rescuer_id, "action": action})

    return ModerationActionResponse(success=True, message=message, action=action)


@router.post("/rescuers/{rescuer_id}/flag", response_model=ModerationActionResponse)
async def flag_rescuer(rescuer_id: str, request: FlagRequest) -> ModerationActionResponse:
    """Flag a rescuer for review."""
    rescuer = _find_rescuer(rescuer_id)
    rescuer["flag_count"] = rescuer.get("flag_count", 0) + 1

    action = ModerationAction.FLAG
    message = f"Rescuer '{rescuer['name']}' flagged for review"

    _log_action(action, "rescuer", rescuer_id, rescuer["name"], request.details)
    logger.info(message, extra={"rescuer_id": rescuer_id, "reason": request.reason})

    return ModerationActionResponse(success=True, message=message, action=action)


@router.post("/rescuers/bulk", response_model=BulkActionResponse)
async def bulk_action(request: BulkActionRequest) -> BulkActionResponse:
    """Perform bulk moderation actions on rescuers."""
    processed = 0
    failed = 0
    errors: list[str] = []

    action_map = {
        BulkActionType.VERIFY: (
            ModerationAction.VERIFY,
            "verification_status",
            VerificationStatus.VERIFIED,
        ),
        BulkActionType.UNVERIFY: (
            ModerationAction.UNVERIFY,
            "verification_status",
            VerificationStatus.UNVERIFIED,
        ),
        BulkActionType.SUSPEND: (ModerationAction.SUSPEND, "status", RescuerStatus.SUSPENDED),
        BulkActionType.UNSUSPEND: (ModerationAction.UNSUSPEND, "status", RescuerStatus.ACTIVE),
    }

    mod_action, field, value = action_map[request.action]

    for rescuer_id in request.rescuer_ids:
        try:
            rescuer = _find_rescuer(rescuer_id)
            rescuer[field] = value
            _log_action(mod_action, "rescuer", rescuer_id, rescuer["name"], request.reason)
            processed += 1
        except HTTPException:
            failed += 1
            errors.append(f"Rescuer '{rescuer_id}' not found")

    return BulkActionResponse(processed=processed, failed=failed, errors=errors)


# ---------------------------------------------------------------------------
# Endpoints — Campaigns
# ---------------------------------------------------------------------------


@router.get("/campaigns", response_model=CampaignListResponse)
async def list_campaigns(
    status_filter: CampaignStatus | None = Query(None, alias="status"),
) -> CampaignListResponse:
    """List campaigns pending moderation."""
    filtered = list(SAMPLE_CAMPAIGNS)

    if status_filter:
        filtered = [c for c in filtered if c["status"] == status_filter]

    return CampaignListResponse(
        campaigns=[CampaignModerationInfo(**c) for c in filtered],
        total=len(filtered),
    )


@router.post("/campaigns/{campaign_id}/review", response_model=ModerationActionResponse)
async def review_campaign(
    campaign_id: str, request: CampaignReviewRequest
) -> ModerationActionResponse:
    """Approve or reject a campaign."""
    campaign = None
    for c in SAMPLE_CAMPAIGNS:
        if c["id"] == campaign_id:
            campaign = c
            break

    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign '{campaign_id}' not found",
        )

    if request.approve:
        campaign["status"] = CampaignStatus.APPROVED
        action = ModerationAction.APPROVE_CAMPAIGN
        message = f"Campaign '{campaign['title']}' approved"
    else:
        campaign["status"] = CampaignStatus.REJECTED
        action = ModerationAction.REJECT_CAMPAIGN
        message = f"Campaign '{campaign['title']}' rejected"

    _log_action(action, "campaign", campaign_id, campaign["title"], request.reason)
    logger.info(message, extra={"campaign_id": campaign_id})

    return ModerationActionResponse(success=True, message=message, action=action)


# ---------------------------------------------------------------------------
# Endpoints — Flags
# ---------------------------------------------------------------------------


@router.get("/flags", response_model=FlagListResponse)
async def list_flags(
    status_filter: FlagStatus | None = Query(None, alias="status"),
) -> FlagListResponse:
    """List content flags."""
    filtered = list(SAMPLE_FLAGS)

    if status_filter:
        filtered = [f for f in filtered if f["status"] == status_filter]

    return FlagListResponse(
        flags=[ContentFlag(**f) for f in filtered],
        total=len(filtered),
    )


@router.post("/flags/{flag_id}/review", response_model=ModerationActionResponse)
async def review_flag(flag_id: str, request: FlagReviewRequest) -> ModerationActionResponse:
    """Review a content flag."""
    flag = None
    for f in SAMPLE_FLAGS:
        if f["id"] == flag_id:
            flag = f
            break

    if flag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flag '{flag_id}' not found",
        )

    now = datetime.now(UTC).isoformat()

    if request.action == "dismiss":
        flag["status"] = FlagStatus.DISMISSED
        action = ModerationAction.DISMISS_FLAG
        message = f"Flag '{flag_id}' dismissed"
    else:
        flag["status"] = FlagStatus.ACTION_TAKEN
        action = ModerationAction.REMOVE_CONTENT
        message = f"Flag '{flag_id}' — action taken: {request.action}"

    flag["reviewed_at"] = now
    flag["reviewed_by"] = "admin-001"
    flag["resolution"] = request.reason

    _log_action(
        action, "flag", flag_id, f"{flag['content_type']}:{flag['content_id']}", request.reason
    )
    logger.info(message, extra={"flag_id": flag_id})

    return ModerationActionResponse(success=True, message=message, action=action)


# ---------------------------------------------------------------------------
# Endpoints — History
# ---------------------------------------------------------------------------


@router.get("/history", response_model=ModerationHistoryResponse)
async def get_moderation_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
) -> ModerationHistoryResponse:
    """Get moderation action history."""
    sorted_log = sorted(_moderation_log, key=lambda e: e["timestamp"], reverse=True)
    total = len(sorted_log)
    start = (page - 1) * page_size
    page_items = sorted_log[start : start + page_size]

    return ModerationHistoryResponse(
        entries=[ModerationLogEntry(**e) for e in page_items],
        total=total,
    )
