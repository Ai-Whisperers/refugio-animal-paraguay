"""Service layer for GDPR data deletion (right to erasure).

Implements the EU right to be forgotten by anonymizing personal data across
all tables while preserving non-personal records needed for operational
integrity (adoption history, donation totals for financial reporting).

Strategy: anonymize rather than hard-delete to maintain referential integrity.
Personal fields are replaced with "[DELETED]" and unique fields get a UUID suffix
to avoid constraint violations.
"""

import logging
from uuid import UUID, uuid4

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.adopter import Adopter
from src.db.models.donation import Donor
from src.db.models.notification import Notification
from src.db.models.user import User
from src.db.models.user_consent import UserConsent

logger = logging.getLogger(__name__)

ANONYMIZED_NAME = "[DELETED]"
ANONYMIZED_PHONE = None
ANONYMIZED_ADDRESS = None


def _anonymized_email() -> str:
    """Generate a unique anonymized email to avoid UNIQUE constraint violations."""
    return f"deleted-{uuid4().hex[:12]}@anonymized.invalid"


async def anonymize_donor(db: AsyncSession, donor_id: UUID) -> bool:
    """Anonymize a donor's personal data while preserving donation records.

    Returns True if donor was found and anonymized, False if not found.
    """
    donor = await db.get(Donor, donor_id)
    if donor is None:
        return False

    donor.full_name = ANONYMIZED_NAME
    donor.email = _anonymized_email()
    donor.country = None
    donor.gdpr_consent_at = None
    await db.flush()

    logger.info("Anonymized donor %s", donor_id)
    return True


async def anonymize_adopter(db: AsyncSession, adopter_id: UUID) -> bool:
    """Anonymize an adopter's personal data while preserving adoption records.

    Returns True if adopter was found and anonymized, False if not found.
    """
    adopter = await db.get(Adopter, adopter_id)
    if adopter is None:
        return False

    adopter.full_name = ANONYMIZED_NAME
    adopter.email = _anonymized_email()
    adopter.phone = ANONYMIZED_PHONE
    adopter.address = ANONYMIZED_ADDRESS
    adopter.gdpr_consent_at = None
    await db.flush()

    logger.info("Anonymized adopter %s", adopter_id)
    return True


async def delete_user_consents(db: AsyncSession, user_id: UUID) -> int:
    """Delete all consent records for a user. Returns count of deleted records."""
    result = await db.execute(delete(UserConsent).where(UserConsent.user_id == user_id))
    count = result.rowcount
    if count > 0:
        logger.info("Deleted %d consent records for user %s", count, user_id)
    return count


async def delete_user_notifications(db: AsyncSession, user_id: UUID) -> int:
    """Delete all notifications for a user. Returns count of deleted records."""
    result = await db.execute(delete(Notification).where(Notification.user_id == user_id))
    count = result.rowcount
    if count > 0:
        logger.info("Deleted %d notifications for user %s", count, user_id)
    return count


async def deactivate_user_account(db: AsyncSession, user_id: UUID) -> bool:
    """Deactivate and anonymize a user account.

    Returns True if user was found and deactivated, False if not found.
    """
    user = await db.get(User, user_id)
    if user is None:
        return False

    user.email = _anonymized_email()
    user.is_active = False
    await db.flush()

    logger.info("Deactivated and anonymized user account %s", user_id)
    return True


async def process_deletion_request(
    db: AsyncSession,
    user_id: UUID,
    donor_id: UUID | None = None,
    adopter_id: UUID | None = None,
) -> dict:
    """Process a full GDPR deletion request for a user.

    Anonymizes personal data across all relevant tables.
    Returns a summary of actions taken.
    """
    summary: dict = {
        "user_id": str(user_id),
        "user_deactivated": False,
        "consents_deleted": 0,
        "notifications_deleted": 0,
        "donor_anonymized": False,
        "adopter_anonymized": False,
    }

    # Deactivate and anonymize the user account
    summary["user_deactivated"] = await deactivate_user_account(db, user_id)

    # Delete consent records
    summary["consents_deleted"] = await delete_user_consents(db, user_id)

    # Delete notifications
    summary["notifications_deleted"] = await delete_user_notifications(db, user_id)

    # Anonymize donor profile if linked
    if donor_id is not None:
        summary["donor_anonymized"] = await anonymize_donor(db, donor_id)

    # Anonymize adopter profile if linked
    if adopter_id is not None:
        summary["adopter_anonymized"] = await anonymize_adopter(db, adopter_id)

    logger.info("GDPR deletion request processed for user %s: %s", user_id, summary)
    return summary
