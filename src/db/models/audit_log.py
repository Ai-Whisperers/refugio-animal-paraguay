"""SQLAlchemy ORM model for the audit trail system.

Records every authenticated action for GDPR Article 30 compliance.
Each entry captures who did what, to which resource, when, and from where.
"""

import enum
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class AuditAction(enum.StrEnum):
    """Action types tracked in the audit trail."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    APPROVE = "approve"
    REJECT = "reject"
    ASSIGN = "assign"
    EXPORT = "export"
    GENERATE_REPORT = "generate_report"
    LOGIN = "login"
    LOGOUT = "logout"
    GDPR_ERASURE = "gdpr_erasure"


class AuditLog(Base):
    """Immutable audit trail entry.

    Captures every authenticated action for compliance and accountability.
    Entries are append-only; they must never be updated or deleted.
    """

    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    user_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
    )
    resource_type: Mapped[str] = mapped_column(
        sa.String(100),
        nullable=False,
    )
    resource_id: Mapped[str | None] = mapped_column(
        sa.String(255),
        nullable=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    ip_address: Mapped[str | None] = mapped_column(
        sa.String(45),
        nullable=True,
    )
    user_agent: Mapped[str | None] = mapped_column(
        sa.String(500),
        nullable=True,
    )
    old_values: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    new_values: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    request_id: Mapped[str | None] = mapped_column(
        sa.String(36),
        nullable=True,
    )

    __table_args__ = (
        sa.Index("ix_audit_logs_user_timestamp", "user_id", "timestamp"),
        sa.Index(
            "ix_audit_logs_resource_timestamp",
            "resource_type",
            "resource_id",
            "timestamp",
        ),
        sa.Index("ix_audit_logs_timestamp", "timestamp"),
    )
