"""SQLAlchemy ORM models for email list management and segmentation.

Supports creation of subscriber lists with segmentation by user type
(donors, adopters, volunteers, etc.) and unsubscribe token tracking
for GDPR-compliant opt-out flows.
"""

import enum
import secrets
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class EmailListType(enum.StrEnum):
    """Category of email list for segmentation purposes."""

    GENERAL = "general"
    DONORS = "donors"
    ADOPTERS = "adopters"
    VOLUNTEERS = "volunteers"
    FOSTERS = "fosters"
    RESCUERS = "rescuers"
    CUSTOM = "custom"


class EmailListStatus(enum.StrEnum):
    """Lifecycle status of an email list."""

    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class MemberStatus(enum.StrEnum):
    """Subscription status of a list member."""

    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"
    COMPLAINED = "complained"


def _generate_unsubscribe_token() -> str:
    """Generate a cryptographically secure unsubscribe token."""
    return secrets.token_urlsafe(32)


class EmailList(Base):
    """A named list of email subscribers used for campaign targeting.

    Staff create lists manually or via segmentation rules. Lists can be
    targeted by user type to auto-populate subscribers from existing
    donor/adopter/volunteer records.
    """

    __tablename__ = "email_lists"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    list_type: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        default=EmailListType.GENERAL,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        default=EmailListStatus.ACTIVE,
        index=True,
    )
    created_by_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )

    members: Mapped[list["EmailListMember"]] = relationship(
        "EmailListMember",
        back_populates="email_list",
        cascade="all, delete-orphan",
        lazy="select",
    )

    @property
    def subscriber_count(self) -> int:
        """Count of currently subscribed (active) members."""
        return sum(1 for m in self.members if m.status == MemberStatus.SUBSCRIBED)


class EmailListMember(Base):
    """A subscriber entry within an email list.

    Stores the email address, display name, subscription status, and
    a unique unsubscribe token for GDPR-compliant opt-out links. An
    email address may appear in multiple lists with independent status.
    """

    __tablename__ = "email_list_members"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    email_list_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("email_lists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        sa.String(320),
        nullable=False,
        index=True,
    )
    name: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        default=MemberStatus.SUBSCRIBED,
        index=True,
    )
    unsubscribe_token: Mapped[str] = mapped_column(
        sa.String(64),
        nullable=False,
        unique=True,
        default=_generate_unsubscribe_token,
    )
    # Optional link to source entity
    source_type: Mapped[str | None] = mapped_column(
        sa.String(50),
        nullable=True,
        comment="Origin entity type: donor, adopter, volunteer, rescuer, manual",
    )
    source_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=True,
        comment="UUID of the source entity if auto-populated from segmentation",
    )
    subscribed_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    unsubscribed_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=True,
    )

    email_list: Mapped["EmailList"] = relationship(
        "EmailList",
        back_populates="members",
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "email_list_id",
            "email",
            name="uq_email_list_member_email",
        ),
    )
