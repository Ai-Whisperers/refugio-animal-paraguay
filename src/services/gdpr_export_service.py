"""Business logic for GDPR data export (Articles 15 & 20).

Aggregates personal data across all tables for a given data subject
(donor, adopter, or staff member) and produces a structured JSON export.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.adopter import Adopter
from src.db.models.adoption_request import AdoptionRequest
from src.db.models.audit_log import AuditLog
from src.db.models.contact_submission import ContactSubmission
from src.db.models.data_export import DataExportRequest, DataExportStatus, DataSubjectType
from src.db.models.donation import Donation, Donor
from src.db.models.in_kind_donation import InKindDonation
from src.db.models.user import User
from src.db.models.user_consent import UserConsent

logger = logging.getLogger(__name__)

EXPORT_EXPIRY_DAYS = 7


async def create_export_request(
    db: AsyncSession,
    subject_type: str,
    subject_id: UUID,
    subject_email: str,
    requested_by_user_id: UUID | None = None,
) -> DataExportRequest:
    """Create and immediately process a data export request.

    The export is generated synchronously for now. Future iterations
    may move processing to a background job.
    """
    export_req = DataExportRequest(
        requested_by_user_id=requested_by_user_id,
        subject_type=subject_type,
        subject_id=subject_id,
        subject_email=subject_email,
        status=DataExportStatus.PROCESSING.value,
        expires_at=datetime.now(UTC) + timedelta(days=EXPORT_EXPIRY_DAYS),
    )
    db.add(export_req)
    await db.flush()

    try:
        export_data = await _aggregate_subject_data(db, subject_type, subject_id)
        export_req.export_data = export_data
        export_req.status = DataExportStatus.COMPLETED.value
        export_req.completed_at = datetime.now(UTC)
    except Exception:
        logger.exception("Data export failed for %s %s", subject_type, subject_id)
        export_req.status = DataExportStatus.FAILED.value
        export_req.error_message = "Export generation failed"

    await db.flush()
    logger.info("Data export %s for %s %s: %s", export_req.id, subject_type, subject_id, export_req.status)
    return export_req


async def get_export_request(
    db: AsyncSession,
    export_id: UUID,
) -> DataExportRequest | None:
    """Get an export request by ID."""
    return await db.get(DataExportRequest, export_id)


async def mark_downloaded(
    db: AsyncSession,
    export_req: DataExportRequest,
) -> DataExportRequest:
    """Mark an export as downloaded."""
    export_req.downloaded_at = datetime.now(UTC)
    await db.flush()
    return export_req


async def list_export_requests(
    db: AsyncSession,
    subject_type: str | None = None,
    subject_id: UUID | None = None,
    requested_by_user_id: UUID | None = None,
) -> list[DataExportRequest]:
    """List export requests with optional filters."""
    stmt = select(DataExportRequest).order_by(DataExportRequest.requested_at.desc())

    if subject_type is not None:
        stmt = stmt.where(DataExportRequest.subject_type == subject_type)
    if subject_id is not None:
        stmt = stmt.where(DataExportRequest.subject_id == subject_id)
    if requested_by_user_id is not None:
        stmt = stmt.where(DataExportRequest.requested_by_user_id == requested_by_user_id)

    result = await db.execute(stmt)
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Data aggregation per subject type
# ---------------------------------------------------------------------------


async def _aggregate_subject_data(
    db: AsyncSession,
    subject_type: str,
    subject_id: UUID,
) -> dict:
    """Aggregate all personal data for a data subject."""
    if subject_type == DataSubjectType.DONOR:
        return await _aggregate_donor_data(db, subject_id)
    if subject_type == DataSubjectType.ADOPTER:
        return await _aggregate_adopter_data(db, subject_id)
    if subject_type == DataSubjectType.STAFF:
        return await _aggregate_staff_data(db, subject_id)

    msg = f"Unknown subject type: {subject_type}"
    raise ValueError(msg)


async def _aggregate_donor_data(db: AsyncSession, donor_id: UUID) -> dict:
    """Aggregate all personal data for a donor."""
    donor = await db.get(Donor, donor_id)
    if donor is None:
        return {"error": "Donor not found", "subject_type": "donor", "subject_id": str(donor_id)}

    # Monetary donations
    donations_result = await db.execute(
        select(Donation).where(Donation.donor_id == donor_id).order_by(Donation.created_at.desc())
    )
    donations = list(donations_result.scalars().all())

    # In-kind donations
    in_kind_result = await db.execute(
        select(InKindDonation).where(InKindDonation.donor_id == donor_id).order_by(InKindDonation.created_at.desc())
    )
    in_kind_donations = list(in_kind_result.scalars().all())

    # Contact submissions by email
    contacts_result = await db.execute(
        select(ContactSubmission)
        .where(ContactSubmission.visitor_email == donor.email)
        .order_by(ContactSubmission.created_at.desc())
    )
    contacts = list(contacts_result.scalars().all())

    return {
        "export_type": "gdpr_data_export",
        "subject_type": "donor",
        "export_date": datetime.now(UTC).isoformat(),
        "profile": {
            "id": str(donor.id),
            "full_name": donor.full_name,
            "email": donor.email,
            "country": donor.country,
            "currency_preference": donor.currency_preference,
            "gdpr_consent_at": donor.gdpr_consent_at.isoformat() if donor.gdpr_consent_at else None,
            "created_at": donor.created_at.isoformat(),
            "updated_at": donor.updated_at.isoformat(),
        },
        "donations": [
            {
                "id": str(d.id),
                "amount_cents": d.amount_cents,
                "currency": d.currency,
                "payment_method": d.payment_method,
                "status": d.status,
                "receipt_number": d.receipt_number,
                "notes": d.notes,
                "created_at": d.created_at.isoformat(),
            }
            for d in donations
        ],
        "in_kind_donations": [
            {
                "id": str(ik.id),
                "item_type": ik.item_type,
                "description": ik.description,
                "quantity": ik.quantity,
                "estimated_value_cents": ik.estimated_value_cents,
                "currency": ik.currency,
                "date_received": ik.date_received.isoformat(),
                "notes": ik.notes,
                "created_at": ik.created_at.isoformat(),
            }
            for ik in in_kind_donations
        ],
        "contact_submissions": [
            {
                "id": str(c.id),
                "subject": c.subject,
                "message": c.message,
                "created_at": c.created_at.isoformat(),
            }
            for c in contacts
        ],
    }


async def _aggregate_adopter_data(db: AsyncSession, adopter_id: UUID) -> dict:
    """Aggregate all personal data for an adopter."""
    adopter = await db.get(Adopter, adopter_id)
    if adopter is None:
        return {"error": "Adopter not found", "subject_type": "adopter", "subject_id": str(adopter_id)}

    # Adoption requests
    requests_result = await db.execute(
        select(AdoptionRequest)
        .where(AdoptionRequest.adopter_id == adopter_id)
        .order_by(AdoptionRequest.created_at.desc())
    )
    adoption_requests = list(requests_result.scalars().all())

    # Contact submissions by email
    contacts_result = await db.execute(
        select(ContactSubmission)
        .where(ContactSubmission.visitor_email == adopter.email)
        .order_by(ContactSubmission.created_at.desc())
    )
    contacts = list(contacts_result.scalars().all())

    return {
        "export_type": "gdpr_data_export",
        "subject_type": "adopter",
        "export_date": datetime.now(UTC).isoformat(),
        "profile": {
            "id": str(adopter.id),
            "full_name": adopter.full_name,
            "email": adopter.email,
            "phone": adopter.phone,
            "address": adopter.address,
            "gdpr_consent_at": adopter.gdpr_consent_at.isoformat() if adopter.gdpr_consent_at else None,
            "created_at": adopter.created_at.isoformat(),
            "updated_at": adopter.updated_at.isoformat(),
        },
        "adoption_requests": [
            {
                "id": str(ar.id),
                "animal_id": str(ar.animal_id),
                "status": ar.status,
                "submitted_at": ar.submitted_at.isoformat(),
                "decided_at": ar.decided_at.isoformat() if ar.decided_at else None,
                "notes": ar.notes,
                "created_at": ar.created_at.isoformat(),
            }
            for ar in adoption_requests
        ],
        "contact_submissions": [
            {
                "id": str(c.id),
                "subject": c.subject,
                "message": c.message,
                "created_at": c.created_at.isoformat(),
            }
            for c in contacts
        ],
    }


async def _aggregate_staff_data(db: AsyncSession, user_id: UUID) -> dict:
    """Aggregate all personal data for a staff member."""
    user = await db.get(User, user_id)
    if user is None:
        return {"error": "User not found", "subject_type": "staff", "subject_id": str(user_id)}

    # Consent records
    consents_result = await db.execute(
        select(UserConsent).where(UserConsent.user_id == user_id).order_by(UserConsent.created_at.desc())
    )
    consents = list(consents_result.scalars().all())

    # Audit log entries where this user is the actor
    audit_result = await db.execute(
        select(AuditLog).where(AuditLog.user_id == user_id).order_by(AuditLog.timestamp.desc()).limit(1000)
    )
    audit_entries = list(audit_result.scalars().all())

    return {
        "export_type": "gdpr_data_export",
        "subject_type": "staff",
        "export_date": datetime.now(UTC).isoformat(),
        "profile": {
            "id": str(user.id),
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
        },
        "consents": [
            {
                "id": str(c.id),
                "consent_type": c.consent_type,
                "status": c.status,
                "opt_in_date": c.opt_in_date.isoformat(),
                "opt_out_date": c.opt_out_date.isoformat() if c.opt_out_date else None,
                "method": c.method,
                "notes": c.notes,
                "created_at": c.created_at.isoformat(),
            }
            for c in consents
        ],
        "audit_trail": [
            {
                "id": str(a.id),
                "action": a.action,
                "resource_type": a.resource_type,
                "resource_id": a.resource_id,
                "timestamp": a.timestamp.isoformat(),
                "ip_address": a.ip_address,
            }
            for a in audit_entries
        ],
    }
