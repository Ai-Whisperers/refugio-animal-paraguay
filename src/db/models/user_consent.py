"""SQLAlchemy ORM model for GDPR consent tracking.

Records explicit user consent for each communication type per GDPR Article 7.
Every consent change (grant or revoke) creates a new record for full audit trail.
"""

import enum
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class ConsentType(enum.StrEnum):
    """Communication types requiring explicit user consent."""

    MARKETING_EMAIL = "marketing_email"
    NEWSLETTER = "newsletter"
    SMS_UPDATES = "sms_updates"
    EVENT_INVITATIONS = "event_invitations"
    DONATION_RECEIPTS = "donation_receipts"


class ConsentStatus(enum.StrEnum):
    """Consent lifecycle status."""

    ACTIVE = "active"
    REVOKED = "revoked"


class ConsentMethod(enum.StrEnum):
    """How the consent was obtained or revoked."""

    USER_SELF_SERVICE = "user_self_service"
    EMAIL_LINK = "email_link"
    STAFF_ASSISTED = "staff_assisted"
    IMPORT_BATCH = "import_batch"


class UserConsent(Base):
    """Individual consent record — one row per consent type per user.

    Each record tracks the current state of a user's consent for a specific
    communication type. History is maintained via the audit trail system.
    """

    __tablename__ = "user_consents"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    user_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    consent_type: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default=ConsentStatus.ACTIVE.value,
    )
    # When consent was first granted
    opt_in_date: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    # When consent was revoked (null if still active)
    opt_out_date: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    # GDPR requires recording context of consent
    ip_address: Mapped[str | None] = mapped_column(
        sa.String(45),
        nullable=True,
    )
    user_agent: Mapped[str | None] = mapped_column(
        sa.String(500),
        nullable=True,
    )
    method: Mapped[str] = mapped_column(
        sa.String(30),
        nullable=False,
        server_default=ConsentMethod.USER_SELF_SERVICE.value,
    )
    # Staff ID when method is staff_assisted
    granted_by_staff_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )

    __table_args__ = (
        # Each user can have at most one consent record per type
        sa.UniqueConstraint("user_id", "consent_type", name="uq_user_consent_type"),
    )
