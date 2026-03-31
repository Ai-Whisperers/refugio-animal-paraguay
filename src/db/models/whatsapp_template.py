"""SQLAlchemy ORM model for WhatsApp message template registry.

Templates must be pre-approved by Meta before they can be sent via the
WhatsApp Cloud API. This model tracks the registration and approval state
of each template so staff can manage and audit template usage.
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class WhatsAppTemplateCategory(StrEnum):
    """Meta-defined template categories determining send restrictions."""

    AUTHENTICATION = "authentication"
    MARKETING = "marketing"
    UTILITY = "utility"


class WhatsAppTemplateStatus(StrEnum):
    """Lifecycle status of a WhatsApp template."""

    PENDING = "pending"  # Submitted to Meta, awaiting review
    APPROVED = "approved"  # Meta approved; ready to send
    REJECTED = "rejected"  # Meta rejected; cannot send
    PAUSED = "paused"  # Temporarily paused by Meta or staff
    DELETED = "deleted"  # Removed from Meta; archived locally


class WhatsAppTemplate(Base):
    """Registry of WhatsApp Business API message templates.

    Templates are created by staff, submitted to Meta for approval, and
    tracked here. Only APPROVED templates can be sent via MetaWhatsAppService.

    The `meta_template_id` field is populated when Meta confirms the template
    creation (returned in the Create Message Template API response).
    """

    __tablename__ = "whatsapp_templates"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )

    # -- Template identity (must match Meta registration exactly) --
    name: Mapped[str] = mapped_column(
        sa.String(512),
        nullable=False,
        comment="Template name as registered in Meta Business Manager (lowercase, underscores)",
    )
    language_code: Mapped[str] = mapped_column(
        sa.String(10),
        nullable=False,
        comment="BCP-47 language code (e.g. 'es', 'en', 'pt_BR')",
    )
    category: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        comment="Meta template category: authentication | marketing | utility",
    )

    # -- Template content --
    header_text: Mapped[str | None] = mapped_column(
        sa.Text,
        nullable=True,
        comment="Optional header text (TEXT header type only)",
    )
    body_text: Mapped[str] = mapped_column(
        sa.Text,
        nullable=False,
        comment="Template body with {{N}} variable placeholders",
    )
    footer_text: Mapped[str | None] = mapped_column(
        sa.Text,
        nullable=True,
        comment="Optional footer text",
    )

    # -- Approval tracking --
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default=sa.text("'pending'"),
        comment="Approval status from Meta",
    )
    meta_template_id: Mapped[str | None] = mapped_column(
        sa.String(255),
        nullable=True,
        unique=True,
        comment="Template ID returned by Meta Cloud API after submission",
    )
    rejection_reason: Mapped[str | None] = mapped_column(
        sa.Text,
        nullable=True,
        comment="Meta rejection reason, if status=rejected",
    )

    # -- Metadata --
    description: Mapped[str | None] = mapped_column(
        sa.Text,
        nullable=True,
        comment="Internal description for staff (not sent to Meta)",
    )
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.true(),
        comment="False = archived; excluded from active template lists",
    )

    # -- Timestamps --
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
    approved_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
        comment="When Meta approved the template (populated by webhook or manual update)",
    )

    __table_args__ = (
        sa.UniqueConstraint("name", "language_code", name="uq_whatsapp_templates_name_lang"),
        sa.CheckConstraint(
            "category IN ('authentication', 'marketing', 'utility')",
            name="chk_whatsapp_templates_category",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'paused', 'deleted')",
            name="chk_whatsapp_templates_status",
        ),
        sa.Index("ix_whatsapp_templates_name", "name"),
        sa.Index("ix_whatsapp_templates_status", "status"),
        sa.Index("ix_whatsapp_templates_name_lang", "name", "language_code"),
    )
