"""Business logic for GDPR data deletion (Article 17 — right to erasure).

Handles deletion request lifecycle, data anonymization for financial records,
and hard deletion of personal data.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.adopter import Adopter
from src.db.models.adoption_request import AdoptionRequest
from src.db.models.contact_submission import ContactSubmission
from src.db.models.deletion_request import DeletionRequest, DeletionRequestStatus
from src.db.models.donation import Donation, Donor
from src.db.models.in_kind_donation import InKindDonation
from src.db.models.user import User

logger = logging.getLogger(__name__)

# Placeholder name used after anonymization
ANONYMOUS_LABEL = "Anonymous (GDPR deleted)"


async def create_deletion_request(
    db: AsyncSession,
    subject_type: str,
    subject_id: UUID,
    subject_email: str,
    reason: str | None = None,
    requested_by_user_id: UUID | None = None,
) -> DeletionRequest:
    """Create a new GDPR deletion request in pending status."""
    deletion_req = DeletionRequest(
        subject_type=subject_type,
        subject_id=subject_id,
        subject_email=subject_email,
        reason=reason,
        status=DeletionRequestStatus.PENDING.value,
        requested_by_user_id=requested_by_user_id,
    )
    db.add(deletion_req)
    await db.flush()

    logger.info(
        "Deletion request %s created for %s %s",
        deletion_req.id,
        subject_type,
        subject_id,
    )
    return deletion_req


async def approve_deletion_request(
    db: AsyncSession,
    request_id: UUID,
    approved_by_user_id: UUID,
) -> DeletionRequest | None:
    """Approve a pending deletion request and execute the deletion.

    Returns None if request not found. Raises ValueError if not in pending status.
    """
    deletion_req = await db.get(DeletionRequest, request_id)
    if deletion_req is None:
        return None

    if deletion_req.status != DeletionRequestStatus.PENDING.value:
        msg = f"Cannot approve request in status: {deletion_req.status}"
        raise ValueError(msg)

    deletion_req.status = DeletionRequestStatus.APPROVED.value
    deletion_req.approved_by_user_id = approved_by_user_id
    deletion_req.approved_at = datetime.now(UTC)
    await db.flush()

    # Execute the deletion immediately after approval
    await _execute_deletion(db, deletion_req)

    deletion_req.status = DeletionRequestStatus.EXECUTED.value
    deletion_req.executed_at = datetime.now(UTC)
    await db.flush()

    logger.info(
        "Deletion request %s executed for %s %s by user %s",
        request_id,
        deletion_req.subject_type,
        deletion_req.subject_id,
        approved_by_user_id,
    )
    return deletion_req


async def deny_deletion_request(
    db: AsyncSession,
    request_id: UUID,
    denied_by_user_id: UUID,
    denial_reason: str | None = None,
) -> DeletionRequest | None:
    """Deny a pending deletion request.

    Returns None if not found. Raises ValueError if not pending.
    """
    deletion_req = await db.get(DeletionRequest, request_id)
    if deletion_req is None:
        return None

    if deletion_req.status != DeletionRequestStatus.PENDING.value:
        msg = f"Cannot deny request in status: {deletion_req.status}"
        raise ValueError(msg)

    deletion_req.status = DeletionRequestStatus.DENIED.value
    deletion_req.approved_by_user_id = denied_by_user_id
    deletion_req.denial_reason = denial_reason
    await db.flush()

    logger.info("Deletion request %s denied", request_id)
    return deletion_req


async def cancel_deletion_request(
    db: AsyncSession,
    request_id: UUID,
) -> DeletionRequest | None:
    """Cancel a pending deletion request.

    Returns None if not found. Raises ValueError if not pending.
    """
    deletion_req = await db.get(DeletionRequest, request_id)
    if deletion_req is None:
        return None

    if deletion_req.status != DeletionRequestStatus.PENDING.value:
        msg = f"Cannot cancel request in status: {deletion_req.status}"
        raise ValueError(msg)

    deletion_req.status = DeletionRequestStatus.CANCELLED.value
    deletion_req.cancelled_at = datetime.now(UTC)
    await db.flush()

    logger.info("Deletion request %s cancelled", request_id)
    return deletion_req


async def get_deletion_request(
    db: AsyncSession,
    request_id: UUID,
) -> DeletionRequest | None:
    """Get a deletion request by ID."""
    return await db.get(DeletionRequest, request_id)


async def list_deletion_requests(
    db: AsyncSession,
    status_filter: str | None = None,
) -> list[DeletionRequest]:
    """List deletion requests with optional status filter."""
    stmt = select(DeletionRequest).order_by(DeletionRequest.requested_at.desc())
    if status_filter is not None:
        stmt = stmt.where(DeletionRequest.status == status_filter)

    result = await db.execute(stmt)
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Deletion execution per subject type
# ---------------------------------------------------------------------------


async def _execute_deletion(
    db: AsyncSession,
    deletion_req: DeletionRequest,
) -> None:
    """Execute the actual data deletion/anonymization."""
    subject_type = deletion_req.subject_type
    subject_id = deletion_req.subject_id

    if subject_type == "donor":
        await _delete_donor(db, subject_id)
    elif subject_type == "adopter":
        await _delete_adopter(db, subject_id)
    elif subject_type == "staff":
        await _delete_staff(db, subject_id)
    else:
        msg = f"Unknown subject type: {subject_type}"
        raise ValueError(msg)


async def _delete_donor(db: AsyncSession, donor_id: UUID) -> None:
    """Delete donor profile, anonymize donation records.

    - Donations: set donor_id=NULL (preserves amount, date, receipt for accounting)
    - In-kind donations: set donor_id=NULL (preserves item records)
    - Contact submissions: hard delete by email
    - Donor profile: hard delete
    """
    donor = await db.get(Donor, donor_id)
    if donor is None:
        return

    donor_email = donor.email

    # Anonymize monetary donations (preserve financial records)
    await db.execute(update(Donation).where(Donation.donor_id == donor_id).values(donor_id=None))

    # Anonymize in-kind donations
    await db.execute(
        update(InKindDonation).where(InKindDonation.donor_id == donor_id).values(donor_id=None)
    )

    # Delete contact submissions by this donor's email
    contacts_result = await db.execute(
        select(ContactSubmission).where(ContactSubmission.visitor_email == donor_email)
    )
    for contact in contacts_result.scalars().all():
        await db.delete(contact)

    # Hard delete donor profile
    await db.delete(donor)
    await db.flush()

    logger.info("Donor %s deleted, donations anonymized", donor_id)


async def _delete_adopter(db: AsyncSession, adopter_id: UUID) -> None:
    """Delete adopter profile, anonymize adoption records.

    - Adoption requests: set adopter_id=NULL (preserves request history)
    - Contact submissions: hard delete by email
    - Adopter profile: hard delete (or soft-delete if already soft-deleted)
    """
    adopter = await db.get(Adopter, adopter_id)
    if adopter is None:
        return

    adopter_email = adopter.email

    # Anonymize adoption requests (preserve animal/status records)
    await db.execute(
        update(AdoptionRequest)
        .where(AdoptionRequest.adopter_id == adopter_id)
        .values(adopter_id=None)
    )

    # Delete contact submissions
    contacts_result = await db.execute(
        select(ContactSubmission).where(ContactSubmission.visitor_email == adopter_email)
    )
    for contact in contacts_result.scalars().all():
        await db.delete(contact)

    # Hard delete adopter profile
    await db.delete(adopter)
    await db.flush()

    logger.info("Adopter %s deleted, adoption requests anonymized", adopter_id)


async def _delete_staff(db: AsyncSession, user_id: UUID) -> None:
    """Deactivate staff account and anonymize profile.

    Staff users cannot be hard-deleted because audit_logs reference them.
    Instead: anonymize email, deactivate account.
    """
    user = await db.get(User, user_id)
    if user is None:
        return

    # Anonymize profile (cannot hard-delete due to audit_log FK)
    user.email = f"deleted-{user_id}@anonymized.local"
    user.hashed_password = (
        "DELETED"  # noqa: S105  # nosec B105 — GDPR erasure placeholder, not a real password
    )
    user.is_active = False
    await db.flush()

    logger.info("Staff user %s anonymized and deactivated", user_id)
