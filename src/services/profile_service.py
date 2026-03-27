"""Profile management service: update profile, change password, GDPR operations."""

import logging
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.utils import hash_password, verify_password
from src.db.models.adopter import Adopter
from src.db.models.adoption_request import AdoptionRequest
from src.db.models.donation import Donation, Donor
from src.db.models.notification_preference import NotificationPreference
from src.db.models.sponsorship import Sponsorship
from src.db.models.user import User
from src.db.models.user_consent import UserConsent
from src.db.models.verification_token import TokenType, VerificationToken

logger = logging.getLogger(__name__)

TOKEN_BYTE_LENGTH = 32
ACCOUNT_DELETION_TOKEN_EXPIRY_HOURS = 24

PREFERENCE_MAP = {
    "email_adoption": ("adoption_status_changed", "email"),
    "email_donations": ("donation_received", "email"),
    "email_volunteer": ("system_alert", "email"),
    "whatsapp_enabled": ("system_alert", "email"),
    "inapp_enabled": ("system_alert", "in_app"),
}


async def update_profile(
    db: AsyncSession,
    user: User,
    full_name: str | None = None,
    phone: str | None = None,
) -> User:
    """Update user profile fields. Only updates provided (non-None) values."""
    if full_name is not None:
        user.full_name = full_name
    if phone is not None:
        user.phone = phone if phone != "" else None
    await db.flush()
    await db.refresh(user)
    logger.info("Profile updated for user %s", str(user.id)[:8] + "...")
    return user


async def change_password(
    db: AsyncSession,
    user: User,
    current_password: str,
    new_password: str,
) -> bool:
    """Change user password after verifying current password."""
    if not verify_password(current_password, user.hashed_password):
        logger.warning("Password change failed: incorrect current password for user %s", str(user.id)[:8] + "...")
        return False
    if verify_password(new_password, user.hashed_password):
        logger.warning("Password change failed: new password same as current for user %s", str(user.id)[:8] + "...")
        return False
    user.hashed_password = hash_password(new_password)
    await db.flush()
    logger.info("Password changed for user %s", str(user.id)[:8] + "...")
    return True


async def get_simple_preferences(db: AsyncSession, user_id: UUID) -> dict[str, bool]:
    """Get simplified notification preferences for the portal UI."""
    result = await db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == user_id)
    )
    prefs = result.scalars().all()
    pref_lookup: dict[tuple[str, str], bool] = {}
    for p in prefs:
        pref_lookup[(p.notification_type, p.channel)] = p.enabled
    simple: dict[str, bool] = {}
    for key, (ntype, channel) in PREFERENCE_MAP.items():
        simple[key] = pref_lookup.get((ntype, channel), True)
    return simple


async def update_simple_preferences(
    db: AsyncSession, user_id: UUID, preferences: dict[str, bool]
) -> dict[str, bool]:
    """Update simplified notification preferences from portal UI."""
    for key, value in preferences.items():
        if key not in PREFERENCE_MAP:
            continue
        ntype, channel = PREFERENCE_MAP[key]
        result = await db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id,
                NotificationPreference.notification_type == ntype,
                NotificationPreference.channel == channel,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.enabled = value
        else:
            db.add(NotificationPreference(
                user_id=user_id, notification_type=ntype, channel=channel, enabled=value,
            ))
    await db.flush()
    logger.info("Preferences updated for user %s", str(user_id)[:8] + "...")
    return await get_simple_preferences(db, user_id)


def _isoformat(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


async def export_user_data(db: AsyncSession, user: User) -> dict:
    """Export all personal data for a user (GDPR Article 15 & 20)."""
    export: dict = {
        "export_date": datetime.now(UTC).isoformat(),
        "user_profile": {
            "id": str(user.id), "full_name": user.full_name, "email": user.email,
            "phone": user.phone, "role": user.role, "is_active": user.is_active,
            "email_verified": user.email_verified,
            "created_at": _isoformat(user.created_at), "updated_at": _isoformat(user.updated_at),
        },
    }

    adopter_result = await db.execute(select(Adopter).where(Adopter.email == user.email))
    adopter = adopter_result.scalar_one_or_none()
    if adopter:
        requests_result = await db.execute(
            select(AdoptionRequest).where(AdoptionRequest.adopter_id == adopter.id)
        )
        export["adoption_requests"] = [
            {"id": str(r.id), "animal_id": str(r.animal_id), "status": r.status, "created_at": _isoformat(r.created_at)}
            for r in requests_result.scalars().all()
        ]
    else:
        export["adoption_requests"] = []

    donor_result = await db.execute(select(Donor).where(Donor.email == user.email))
    donor = donor_result.scalar_one_or_none()
    if donor:
        donations_result = await db.execute(select(Donation).where(Donation.donor_id == donor.id))
        export["donations"] = [
            {"id": str(d.id), "amount_cents": d.amount_cents, "currency": d.currency, "created_at": _isoformat(d.created_at)}
            for d in donations_result.scalars().all()
        ]
        sponsorship_result = await db.execute(select(Sponsorship).where(Sponsorship.donor_id == donor.id))
        export["sponsorships"] = [
            {"id": str(s.id), "animal_id": str(s.animal_id), "tier_id": str(s.tier_id) if s.tier_id else None,
             "status": s.status, "created_at": _isoformat(s.created_at)}
            for s in sponsorship_result.scalars().all()
        ]
    else:
        export["donations"] = []
        export["sponsorships"] = []

    prefs_result = await db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == user.id)
    )
    export["notification_preferences"] = [
        {"notification_type": p.notification_type, "channel": p.channel, "enabled": p.enabled}
        for p in prefs_result.scalars().all()
    ]

    consents_result = await db.execute(select(UserConsent).where(UserConsent.user_id == user.id))
    export["consents"] = [
        {"id": str(c.id), "consent_type": c.consent_type, "status": c.status, "opt_in_date": _isoformat(c.opt_in_date)}
        for c in consents_result.scalars().all()
    ]

    logger.info("GDPR data export generated for user %s", str(user.id)[:8] + "...")
    return export


async def request_account_deletion(db: AsyncSession, user: User, password: str) -> str | None:
    """Initiate account deletion by verifying password and creating confirmation token."""
    if not verify_password(password, user.hashed_password):
        return None

    existing_result = await db.execute(
        select(VerificationToken).where(
            VerificationToken.user_id == user.id,
            VerificationToken.token_type == TokenType.ACCOUNT_DELETION.value,
            VerificationToken.used_at.is_(None),
        )
    )
    for existing in existing_result.scalars().all():
        existing.used_at = datetime.now(UTC)

    token_value = secrets.token_urlsafe(TOKEN_BYTE_LENGTH)
    verification_token = VerificationToken(
        user_id=user.id, token=token_value,
        token_type=TokenType.ACCOUNT_DELETION.value,
        expires_at=datetime.now(UTC) + timedelta(hours=ACCOUNT_DELETION_TOKEN_EXPIRY_HOURS),
    )
    db.add(verification_token)
    await db.flush()
    logger.info("Account deletion requested for user %s", str(user.id)[:8] + "...")
    return token_value


async def confirm_account_deletion(db: AsyncSession, token: str) -> bool:
    """Confirm account deletion using the emailed token."""
    result = await db.execute(
        select(VerificationToken).where(
            VerificationToken.token == token,
            VerificationToken.token_type == TokenType.ACCOUNT_DELETION.value,
            VerificationToken.used_at.is_(None),
        )
    )
    verification_token = result.scalar_one_or_none()
    if verification_token is None:
        return False
    if verification_token.expires_at < datetime.now(UTC):
        return False

    user = await db.get(User, verification_token.user_id)
    if user is None:
        return False

    deleted_placeholder = f"deleted+{user.id}@refugio.local"
    user.full_name = "Deleted User"
    user.email = deleted_placeholder
    user.phone = None
    user.is_active = False
    verification_token.used_at = datetime.now(UTC)
    await db.flush()
    logger.info("Account deletion confirmed for user %s", str(verification_token.user_id)[:8] + "...")
    return True
