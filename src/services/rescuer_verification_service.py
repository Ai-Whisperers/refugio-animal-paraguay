"""Rescuer verification service — submit, review, and manage verification requests.

Handles the full verification lifecycle: rescuers submit evidence,
staff review and approve/reject, and approved profiles get marked as verified.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.rescuer_profile import RescuerProfile
from src.db.models.rescuer_verification import (
    RescuerVerificationRequest,
    VerificationMethod,
    VerificationStatus,
)

logger = logging.getLogger(__name__)

# Constraints
MAX_EVIDENCE_NOTES_LENGTH = 2000
MAX_REVIEWER_NOTES_LENGTH = 2000
MAX_EVIDENCE_URL_LENGTH = 500
MAX_PENDING_REQUESTS_PER_RESCUER = 3

VALID_METHODS = frozenset({m.value for m in VerificationMethod})


class VerificationError(Exception):
    """Base error for verification operations."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class VerificationNotFoundError(VerificationError):
    """Raised when a verification request is not found."""

    def __init__(self, identifier: str) -> None:
        super().__init__(
            message="Verification request not found",
            details=f"No request found for: {identifier}",
        )
        self.identifier = identifier


class RescuerNotFoundError(VerificationError):
    """Raised when the rescuer profile is not found."""

    def __init__(self, user_id: UUID) -> None:
        super().__init__(
            message="Rescuer profile not found",
            details=f"No rescuer profile found for user {user_id}",
        )


class AlreadyVerifiedError(VerificationError):
    """Raised when a rescuer is already verified."""

    def __init__(self) -> None:
        super().__init__(
            message="Already verified",
            details="This rescuer profile is already verified",
        )


class TooManyPendingRequestsError(VerificationError):
    """Raised when too many pending requests exist."""

    def __init__(self) -> None:
        super().__init__(
            message="Too many pending requests",
            details=f"Maximum {MAX_PENDING_REQUESTS_PER_RESCUER} pending requests allowed",
        )


class InvalidReviewTransitionError(VerificationError):
    """Raised when trying to review a non-pending request."""

    def __init__(self, current_status: str) -> None:
        super().__init__(
            message="Cannot review request",
            details=f"Request is already '{current_status}', only pending requests can be reviewed",
        )


def validate_method(method: str) -> None:
    """Validate verification method is one of the allowed values."""
    if method not in VALID_METHODS:
        raise VerificationError(
            message="Invalid verification method",
            details=f"Method must be one of: {', '.join(sorted(VALID_METHODS))}",
        )


def validate_evidence_notes(notes: str | None) -> None:
    """Validate evidence notes length."""
    if notes and len(notes) > MAX_EVIDENCE_NOTES_LENGTH:
        raise VerificationError(
            message="Evidence notes too long",
            details=f"Maximum {MAX_EVIDENCE_NOTES_LENGTH} characters allowed",
        )


def validate_evidence_url(url: str | None) -> None:
    """Validate evidence URL length."""
    if url and len(url) > MAX_EVIDENCE_URL_LENGTH:
        raise VerificationError(
            message="Evidence URL too long",
            details=f"Maximum {MAX_EVIDENCE_URL_LENGTH} characters allowed",
        )


def validate_reviewer_notes(notes: str | None) -> None:
    """Validate reviewer notes length."""
    if notes and len(notes) > MAX_REVIEWER_NOTES_LENGTH:
        raise VerificationError(
            message="Reviewer notes too long",
            details=f"Maximum {MAX_REVIEWER_NOTES_LENGTH} characters allowed",
        )


async def _get_rescuer_profile(db: AsyncSession, user_id: UUID) -> RescuerProfile:
    """Look up the rescuer profile for a user. Raises if not found."""
    result = await db.execute(select(RescuerProfile).where(RescuerProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise RescuerNotFoundError(user_id)
    return profile


async def _count_pending_requests(db: AsyncSession, profile_id: UUID) -> int:
    """Count pending verification requests for a rescuer profile."""
    result = await db.execute(
        select(RescuerVerificationRequest.id).where(
            and_(
                RescuerVerificationRequest.rescuer_profile_id == profile_id,
                RescuerVerificationRequest.status == VerificationStatus.PENDING,
            )
        )
    )
    return len(result.all())


async def submit_verification_request(
    *,
    user_id: UUID,
    method: str,
    evidence_url: str | None = None,
    evidence_notes: str | None = None,
    db: AsyncSession,
) -> RescuerVerificationRequest:
    """Submit a verification request for the authenticated rescuer.

    Raises:
        RescuerNotFoundError: If user has no rescuer profile.
        AlreadyVerifiedError: If rescuer is already verified.
        TooManyPendingRequestsError: If max pending requests reached.
        VerificationError: If validation fails.
    """
    profile = await _get_rescuer_profile(db, user_id)

    if profile.is_verified:
        raise AlreadyVerifiedError()

    validate_method(method)
    validate_evidence_url(evidence_url)
    validate_evidence_notes(evidence_notes)

    pending_count = await _count_pending_requests(db, profile.id)
    if pending_count >= MAX_PENDING_REQUESTS_PER_RESCUER:
        raise TooManyPendingRequestsError()

    request = RescuerVerificationRequest(
        rescuer_profile_id=profile.id,
        method=method,
        evidence_url=evidence_url,
        evidence_notes=evidence_notes,
    )

    db.add(request)
    await db.flush()

    logger.info(
        "Verification request submitted: rescuer=%s method=%s",
        profile.id,
        method,
    )
    return request


async def review_verification_request(
    *,
    request_id: UUID,
    reviewer_user_id: UUID,
    approved: bool,
    reviewer_notes: str | None = None,
    db: AsyncSession,
) -> RescuerVerificationRequest:
    """Review (approve or reject) a pending verification request.

    If approved, also marks the rescuer profile as verified.

    Raises:
        VerificationNotFoundError: If request not found.
        InvalidReviewTransitionError: If request is not pending.
        VerificationError: If validation fails.
    """
    validate_reviewer_notes(reviewer_notes)

    result = await db.execute(
        select(RescuerVerificationRequest).where(RescuerVerificationRequest.id == request_id)
    )
    request = result.scalar_one_or_none()
    if request is None:
        raise VerificationNotFoundError(str(request_id))

    if request.status != VerificationStatus.PENDING:
        raise InvalidReviewTransitionError(request.status)

    new_status = VerificationStatus.APPROVED if approved else VerificationStatus.REJECTED
    request.status = new_status
    request.reviewer_user_id = reviewer_user_id
    request.reviewer_notes = reviewer_notes
    request.reviewed_at = datetime.now(UTC)

    # If approved, mark the rescuer profile as verified
    if approved:
        profile_result = await db.execute(
            select(RescuerProfile).where(RescuerProfile.id == request.rescuer_profile_id)
        )
        profile = profile_result.scalar_one_or_none()
        if profile is not None:
            profile.is_verified = True
            profile.verification_method = request.method

    await db.flush()

    logger.info(
        "Verification request reviewed: request=%s status=%s reviewer=%s",
        request_id,
        new_status,
        reviewer_user_id,
    )
    return request


async def get_verification_request(
    request_id: UUID,
    db: AsyncSession,
) -> RescuerVerificationRequest:
    """Get a single verification request by ID.

    Raises:
        VerificationNotFoundError: If not found.
    """
    result = await db.execute(
        select(RescuerVerificationRequest).where(RescuerVerificationRequest.id == request_id)
    )
    request = result.scalar_one_or_none()
    if request is None:
        raise VerificationNotFoundError(str(request_id))
    return request


async def list_pending_requests(
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0,
) -> list[RescuerVerificationRequest]:
    """List all pending verification requests (for admin review).

    Returns requests ordered by creation date (oldest first).
    """
    result = await db.execute(
        select(RescuerVerificationRequest)
        .where(RescuerVerificationRequest.status == VerificationStatus.PENDING)
        .order_by(RescuerVerificationRequest.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_my_verification_requests(
    user_id: UUID,
    db: AsyncSession,
) -> list[RescuerVerificationRequest]:
    """Get all verification requests for the authenticated rescuer."""
    profile = await _get_rescuer_profile(db, user_id)

    result = await db.execute(
        select(RescuerVerificationRequest)
        .where(RescuerVerificationRequest.rescuer_profile_id == profile.id)
        .order_by(RescuerVerificationRequest.created_at.desc())
    )
    return list(result.scalars().all())
