"""Service layer for GDPR data export (right to access / data portability).

Implements EU GDPR Articles 15 (right of access) and 20 (right to data
portability) by collecting all personal data associated with a user across
all tables and returning it in a structured, machine-readable JSON format.

The export includes: user profile, donor records, adopter records, donation
history, adoption requests, consent records, and notifications.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.adopter import Adopter
from src.db.models.adoption_request import AdoptionRequest
from src.db.models.donation import Donation, Donor
from src.db.models.notification import Notification
from src.db.models.user import User
from src.db.models.user_consent import UserConsent

logger = logging.getLogger(__name__)


def _isoformat(dt: datetime | None) -> str | None:
    """Convert datetime to ISO 8601 string, or None."""
    return dt.isoformat() if dt else None


async def _export_user_profile(db: AsyncSession, user_id: UUID) -> dict | None:
    """Export user account profile data."""
    user = await db.get(User, user_id)
    if user is None:
        return None
    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": _isoformat(user.created_at),
        "updated_at": _isoformat(user.updated_at),
    }


async def _export_donor_data(db: AsyncSession, donor_id: UUID) -> dict | None:
    """Export donor profile and all associated donations."""
    donor = await db.get(Donor, donor_id)
    if donor is None:
        return None

    # Fetch all donations for this donor
    result = await db.execute(select(Donation).where(Donation.donor_id == donor_id))
    donations = result.scalars().all()

    return {
        "profile": {
            "id": str(donor.id),
            "full_name": donor.full_name,
            "email": donor.email,
            "country": donor.country,
            "currency_preference": donor.currency_preference,
            "gdpr_consent_at": _isoformat(donor.gdpr_consent_at),
            "created_at": _isoformat(donor.created_at),
            "updated_at": _isoformat(donor.updated_at),
        },
        "donations": [
            {
                "id": str(d.id),
                "amount_cents": d.amount_cents,
                "currency": d.currency,
                "payment_method": d.payment_method,
                "status": d.status,
                "receipt_number": d.receipt_number,
                "fund_category": d.fund_category,
                "notes": d.notes,
                "created_at": _isoformat(d.created_at),
            }
            for d in donations
        ],
    }


async def _export_adopter_data(db: AsyncSession, adopter_id: UUID) -> dict | None:
    """Export adopter profile and all associated adoption requests."""
    adopter = await db.get(Adopter, adopter_id)
    if adopter is None:
        return None

    # Fetch all adoption requests for this adopter
    result = await db.execute(
        select(AdoptionRequest).where(AdoptionRequest.adopter_id == adopter_id)
    )
    requests = result.scalars().all()

    return {
        "profile": {
            "id": str(adopter.id),
            "full_name": adopter.full_name,
            "email": adopter.email,
            "phone": adopter.phone,
            "address": adopter.address,
            "gdpr_consent_at": _isoformat(adopter.gdpr_consent_at),
            "created_at": _isoformat(adopter.created_at),
            "updated_at": _isoformat(adopter.updated_at),
        },
        "adoption_requests": [
            {
                "id": str(r.id),
                "animal_id": str(r.animal_id),
                "status": r.status,
                "notes": r.notes,
                "created_at": _isoformat(r.created_at),
                "updated_at": _isoformat(r.updated_at),
            }
            for r in requests
        ],
    }


async def _export_consents(db: AsyncSession, user_id: UUID) -> list[dict]:
    """Export all consent records for a user."""
    result = await db.execute(select(UserConsent).where(UserConsent.user_id == user_id))
    consents = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "consent_type": c.consent_type,
            "status": c.status,
            "opt_in_date": _isoformat(c.opt_in_date),
            "opt_out_date": _isoformat(c.opt_out_date),
            "method": c.method,
            "created_at": _isoformat(c.created_at),
        }
        for c in consents
    ]


async def _export_notifications(db: AsyncSession, user_id: UUID) -> list[dict]:
    """Export all notifications for a user."""
    result = await db.execute(select(Notification).where(Notification.user_id == user_id))
    notifications = result.scalars().all()
    return [
        {
            "id": str(n.id),
            "notification_type": n.notification_type,
            "title": n.title,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": _isoformat(n.created_at),
        }
        for n in notifications
    ]


async def generate_data_export(
    db: AsyncSession,
    user_id: UUID,
    donor_id: UUID | None = None,
    adopter_id: UUID | None = None,
) -> dict:
    """Generate a full GDPR data export for a user.

    Collects all personal data across all relevant tables and returns
    a structured dict suitable for JSON serialization.

    Args:
        db: Async database session.
        user_id: The user whose data to export.
        donor_id: Optional linked donor profile ID.
        adopter_id: Optional linked adopter profile ID.

    Returns:
        Dict containing all personal data in a portable format.
    """
    export: dict = {
        "export_metadata": {
            "user_id": str(user_id),
            "generated_at": datetime.now(UTC).isoformat(),
            "format_version": "1.0",
            "gdpr_articles": ["Article 15 (Right of Access)", "Article 20 (Data Portability)"],
        },
        "user_profile": None,
        "donor_data": None,
        "adopter_data": None,
        "consents": [],
        "notifications": [],
    }

    # User profile
    export["user_profile"] = await _export_user_profile(db, user_id)

    # Consent records
    export["consents"] = await _export_consents(db, user_id)

    # Notifications
    export["notifications"] = await _export_notifications(db, user_id)

    # Donor data (if linked)
    if donor_id is not None:
        export["donor_data"] = await _export_donor_data(db, donor_id)

    # Adopter data (if linked)
    if adopter_id is not None:
        export["adopter_data"] = await _export_adopter_data(db, adopter_id)

    logger.info("GDPR data export generated for user %s", user_id)
    return export
