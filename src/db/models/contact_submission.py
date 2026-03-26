"""SQLAlchemy ORM model for contact and inquiry form submissions."""

import enum
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class ContactFormType(enum.StrEnum):
    """Type of form submission."""

    GENERAL = "general"
    ANIMAL_INQUIRY = "animal_inquiry"


class ContactSubmission(Base):
    """Public contact or animal inquiry submission.

    Stores all form submissions from unauthenticated visitors with
    soft-delete support and follow-up tracking.
    """

    __tablename__ = "contact_submissions"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    form_type: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
    )
    # Visitor identification
    visitor_name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    visitor_email: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    # Contact form fields
    subject: Mapped[str | None] = mapped_column(sa.String(200), nullable=True)
    message: Mapped[str] = mapped_column(sa.Text, nullable=False)
    # Animal inquiry fields (null for general contact)
    animal_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("animals.id"),
        nullable=True,
    )
    # Audit fields
    ip_address: Mapped[str | None] = mapped_column(sa.String(45), nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
