"""SQLAlchemy ORM model for newsletter email templates.

Staff create and manage reusable email templates for campaigns.
Templates store subject lines, HTML body, and plain-text fallback.
"""

import enum
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class TemplateStatus(enum.StrEnum):
    """Lifecycle status of an email template."""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class EmailTemplate(Base):
    """A reusable email template for newsletter campaigns.

    Templates are written by staff and can be selected when scheduling
    email campaigns. The HTML body supports variable placeholders using
    {{variable}} syntax for personalisation.
    """

    __tablename__ = "email_templates"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    subject: Mapped[str] = mapped_column(sa.String(500), nullable=False)
    html_body: Mapped[str] = mapped_column(sa.Text, nullable=False)
    text_body: Mapped[str | None] = mapped_column(
        sa.Text,
        nullable=True,
        comment="Plain-text fallback for email clients that do not support HTML",
    )
    status: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        default=TemplateStatus.DRAFT,
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
