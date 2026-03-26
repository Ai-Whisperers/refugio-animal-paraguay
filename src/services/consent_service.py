"""GDPR consent management service.

Provides consent validation (pre-send check) and consent state management.
All consent changes are logged for GDPR Article 7 compliance.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.user_consent import (
    ConsentMethod,
    ConsentStatus,
    ConsentType,
    UserConsent,
)

logger = logging.getLogger(__name__)


async def check_consent(
    db: AsyncSession,
    user_id: UUID,
    consent_type: ConsentType,
) -> bool:
    """Check if a user has active consent for a communication type.

    Returns True if consent is active, False otherwise.
    Use this before sending any communication to verify GDPR compliance.
    """
    stmt = select(UserConsent).where(
        UserConsent.user_id == user_id,
        UserConsent.consent_type == consent_type.value,
        UserConsent.status == ConsentStatus.ACTIVE.value,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def get_user_consents(
    db: AsyncSession,
    user_id: UUID,
) -> list[UserConsent]:
    """Get all consent records for a user."""
    stmt = (
        select(UserConsent).where(UserConsent.user_id == user_id).order_by(UserConsent.consent_type)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_consent_summary(
    db: AsyncSession,
    user_id: UUID,
) -> dict[str, bool]:
    """Get a summary of all consent types with their active status.

    Returns a dict mapping consent_type -> is_active for all known consent types.
    Types without a record default to False (no consent).
    """
    records = await get_user_consents(db, user_id)
    active_types = {r.consent_type for r in records if r.status == ConsentStatus.ACTIVE.value}

    return {ct.value: ct.value in active_types for ct in ConsentType}


async def grant_consent(
    db: AsyncSession,
    user_id: UUID,
    consent_type: ConsentType,
    method: ConsentMethod = ConsentMethod.USER_SELF_SERVICE,
    ip_address: str | None = None,
    user_agent: str | None = None,
    granted_by_staff_id: UUID | None = None,
    notes: str | None = None,
) -> UserConsent:
    """Grant consent for a communication type. Idempotent if already active.

    Creates a new consent record or reactivates a revoked one.
    """
    # Check for existing record
    stmt = select(UserConsent).where(
        UserConsent.user_id == user_id,
        UserConsent.consent_type == consent_type.value,
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing is not None:
        if existing.status == ConsentStatus.ACTIVE.value:
            # Already active — idempotent, no change needed
            logger.info(
                "Consent already active: user=%s type=%s",
                user_id,
                consent_type.value,
            )
            return existing

        # Reactivate revoked consent
        existing.status = ConsentStatus.ACTIVE.value
        existing.opt_in_date = datetime.now(UTC)
        existing.opt_out_date = None
        existing.method = method.value
        existing.ip_address = ip_address
        existing.user_agent = user_agent
        existing.granted_by_staff_id = granted_by_staff_id
        existing.notes = notes
        await db.flush()
        await db.refresh(existing)

        logger.info(
            "Consent reactivated: user=%s type=%s method=%s",
            user_id,
            consent_type.value,
            method.value,
        )
        return existing

    # Create new consent record
    consent = UserConsent(
        user_id=user_id,
        consent_type=consent_type.value,
        status=ConsentStatus.ACTIVE.value,
        method=method.value,
        ip_address=ip_address,
        user_agent=user_agent,
        granted_by_staff_id=granted_by_staff_id,
        notes=notes,
    )
    db.add(consent)
    await db.flush()
    await db.refresh(consent)

    logger.info(
        "Consent granted: user=%s type=%s method=%s",
        user_id,
        consent_type.value,
        method.value,
    )
    return consent


async def revoke_consent(
    db: AsyncSession,
    user_id: UUID,
    consent_type: ConsentType,
    method: ConsentMethod = ConsentMethod.USER_SELF_SERVICE,
    ip_address: str | None = None,
    user_agent: str | None = None,
    notes: str | None = None,
) -> UserConsent | None:
    """Revoke consent for a communication type.

    Returns the updated record, or None if no consent record exists.
    Idempotent if already revoked.
    """
    stmt = select(UserConsent).where(
        UserConsent.user_id == user_id,
        UserConsent.consent_type == consent_type.value,
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing is None:
        logger.warning(
            "Cannot revoke non-existent consent: user=%s type=%s",
            user_id,
            consent_type.value,
        )
        return None

    if existing.status == ConsentStatus.REVOKED.value:
        # Already revoked — idempotent
        logger.info(
            "Consent already revoked: user=%s type=%s",
            user_id,
            consent_type.value,
        )
        return existing

    existing.status = ConsentStatus.REVOKED.value
    existing.opt_out_date = datetime.now(UTC)
    existing.method = method.value
    existing.ip_address = ip_address
    existing.user_agent = user_agent
    existing.notes = notes
    await db.flush()
    await db.refresh(existing)

    logger.info(
        "Consent revoked: user=%s type=%s method=%s",
        user_id,
        consent_type.value,
        method.value,
    )
    return existing
