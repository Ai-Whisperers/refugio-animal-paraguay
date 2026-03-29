"""Service layer for GDPR data deletion (right to erasure).

Implements the EU right to be forgotten by anonymizing personal data across
all tables while preserving non-personal records needed for operational
integrity (adoption history, donation totals for financial reporting).

Strategy: anonymize rather than hard-delete to maintain referential integrity.
Personal fields are replaced with "[DELETED]" and unique fields get a UUID suffix
to avoid constraint violations.

Covered entities (Article 17 scope):
- User account (email, full_name, phone, deactivation)
- Donor profile (full_name, email, country, GDPR consent timestamp)
- Adopter profile (full_name, email, phone, address, GDPR consent timestamp)
- Volunteer profile (emergency contact name/phone, bio, motivation)
- Rescuer profile (display_name, slug, bio, location, social links, WhatsApp)
- Foster profile (motivation, experience description, other_pets_description)
- Consent records (hard delete)
- Notification records (hard delete)
"""

import logging
from uuid import UUID, uuid4

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.adopter import Adopter
from src.db.models.donation import Donor
from src.db.models.foster_profile import FosterProfile
from src.db.models.notification import Notification
from src.db.models.rescuer_profile import RescuerProfile
from src.db.models.user import User
from src.db.models.user_consent import UserConsent
from src.db.models.volunteer_profile import VolunteerProfile

logger = logging.getLogger(__name__)

ANONYMIZED_NAME = "[DELETED]"
ANONYMIZED_PHONE = None
ANONYMIZED_ADDRESS = None
ANONYMIZED_TEXT = "[DELETED]"


def _anonymized_email() -> str:
    """Generate a unique anonymized email to avoid UNIQUE constraint violations."""
    return f"deleted-{uuid4().hex[:12]}@anonymized.invalid"


def _anonymized_slug() -> str:
    """Generate a unique anonymized slug to avoid UNIQUE constraint violations."""
    return f"deleted-{uuid4().hex[:16]}"


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


async def anonymize_volunteer(db: AsyncSession, volunteer_id: UUID) -> bool:
    """Anonymize a volunteer profile's personal data while preserving hours/certificates.

    Clears emergency contact details, bio, and motivation text.
    Sets status to inactive so the record can no longer be used.
    Returns True if volunteer was found and anonymized, False if not found.
    """
    volunteer = await db.get(VolunteerProfile, volunteer_id)
    if volunteer is None:
        return False

    volunteer.emergency_contact_name = None
    volunteer.emergency_contact_phone = None
    volunteer.bio = None
    volunteer.motivation = ANONYMIZED_TEXT
    volunteer.status = "inactive"
    await db.flush()

    logger.info("Anonymized volunteer profile %s", volunteer_id)
    return True


async def anonymize_rescuer(db: AsyncSession, rescuer_id: UUID) -> bool:
    """Anonymize a rescuer profile's personal data while preserving animal records.

    Clears display name, bio, location, social links, and WhatsApp number.
    Generates a unique anonymous slug to avoid UNIQUE constraint violations.
    Returns True if rescuer was found and anonymized, False if not found.
    """
    rescuer = await db.get(RescuerProfile, rescuer_id)
    if rescuer is None:
        return False

    rescuer.display_name = ANONYMIZED_NAME
    rescuer.slug = _anonymized_slug()
    rescuer.bio = None
    rescuer.location_city = None
    rescuer.location_coords = None
    rescuer.social_links = None
    rescuer.phone_whatsapp = None
    await db.flush()

    logger.info("Anonymized rescuer profile %s", rescuer_id)
    return True


async def anonymize_foster(db: AsyncSession, foster_id: UUID) -> bool:
    """Anonymize a foster profile's personal data while preserving placement history.

    Clears motivation, experience description, and other pets description.
    Sets status to inactive so the profile can no longer be used.
    Returns True if foster was found and anonymized, False if not found.
    """
    foster = await db.get(FosterProfile, foster_id)
    if foster is None:
        return False

    foster.motivation = ANONYMIZED_TEXT
    foster.experience_description = None
    foster.other_pets_description = None
    foster.status = "inactive"
    await db.flush()

    logger.info("Anonymized foster profile %s", foster_id)
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

    Clears email, full_name, and phone to remove all PII from the account record.
    Returns True if user was found and deactivated, False if not found.
    """
    user = await db.get(User, user_id)
    if user is None:
        return False

    user.email = _anonymized_email()
    user.full_name = None
    user.phone = None
    user.is_active = False
    await db.flush()

    logger.info("Deactivated and anonymized user account %s", user_id)
    return True


async def process_deletion_request(
    db: AsyncSession,
    user_id: UUID,
    donor_id: UUID | None = None,
    adopter_id: UUID | None = None,
    volunteer_id: UUID | None = None,
    rescuer_id: UUID | None = None,
    foster_id: UUID | None = None,
) -> dict:
    """Process a full GDPR deletion request for a user.

    Performs third-party deletion cascade (Stripe, email lists) BEFORE anonymizing
    the donor record, so that the original email/stripe_customer_id are still
    available to identify the records to delete externally.

    Anonymizes personal data across all relevant tables.
    Returns a summary of actions taken.

    Covered entities: user account, donor profile, adopter profile,
    volunteer profile, rescuer profile, foster profile, consents, notifications.
    """
    from src.services.gdpr_third_party_deletion_service import process_third_party_deletion

    summary: dict = {
        "user_id": str(user_id),
        "user_deactivated": False,
        "consents_deleted": 0,
        "notifications_deleted": 0,
        "donor_anonymized": False,
        "adopter_anonymized": False,
        "volunteer_anonymized": False,
        "rescuer_anonymized": False,
        "foster_anonymized": False,
        "stripe_subscriptions_cancelled": 0,
        "stripe_subscriptions_failed": 0,
        "stripe_customer_deleted": False,
        "email_lists_removed": 0,
    }

    # Third-party deletion cascade happens FIRST — before we anonymize the donor email
    if donor_id is not None:
        donor = await db.get(Donor, donor_id)
        donor_email = donor.email if donor is not None else None
        stripe_customer_id = donor.stripe_customer_id if donor is not None else None

        third_party = await process_third_party_deletion(
            db,
            donor_id=donor_id,
            donor_email=donor_email,
            stripe_customer_id=stripe_customer_id,
        )
        summary["stripe_subscriptions_cancelled"] = third_party["stripe_subscriptions_cancelled"]
        summary["stripe_subscriptions_failed"] = third_party["stripe_subscriptions_failed"]
        summary["stripe_customer_deleted"] = third_party["stripe_customer_deleted"]
        summary["email_lists_removed"] = third_party["email_lists_removed"]

    # Deactivate and anonymize the user account (email, full_name, phone)
    summary["user_deactivated"] = await deactivate_user_account(db, user_id)

    # Delete consent records (hard delete — no need to preserve)
    summary["consents_deleted"] = await delete_user_consents(db, user_id)

    # Delete notifications (hard delete — no need to preserve)
    summary["notifications_deleted"] = await delete_user_notifications(db, user_id)

    # Anonymize donor profile if linked (after third-party cascade)
    if donor_id is not None:
        summary["donor_anonymized"] = await anonymize_donor(db, donor_id)

    # Anonymize adopter profile if linked
    if adopter_id is not None:
        summary["adopter_anonymized"] = await anonymize_adopter(db, adopter_id)

    # Anonymize volunteer profile if linked
    if volunteer_id is not None:
        summary["volunteer_anonymized"] = await anonymize_volunteer(db, volunteer_id)

    # Anonymize rescuer profile if linked
    if rescuer_id is not None:
        summary["rescuer_anonymized"] = await anonymize_rescuer(db, rescuer_id)

    # Anonymize foster profile if linked
    if foster_id is not None:
        summary["foster_anonymized"] = await anonymize_foster(db, foster_id)

    logger.info("GDPR deletion request processed for user %s: %s", user_id, summary)
    return summary
