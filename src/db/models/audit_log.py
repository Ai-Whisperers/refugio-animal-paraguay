"""SQLAlchemy ORM model for the audit trail system.

Records all authenticated actions for GDPR Article 30 compliance.
Each entry captures who did what, when, to which resource, and from where.
"""

import enum
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class AuditAction(enum.StrEnum):
    """Actions that can be recorded in the audit trail."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    APPROVE = "approve"
    REJECT = "reject"
    ASSIGN = "assign"
    EXPORT = "export"
    LOGIN = "login"
    LOGOUT = "logout"


class ResourceType(enum.StrEnum):
    """Resource types that can appear in audit log entries."""

    ANIMAL = "animal"
    ADOPTER = "adopter"
    ADOPTION_REQUEST = "adoption_request"
    DONOR = "donor"
    DONATION = "donation"
    USER = "user"
    PHOTO = "photo"
    SYSTEM = "system"


# Map HTTP methods to audit actions
HTTP_METHOD_TO_ACTION: dict[str, AuditAction] = {
    "POST": AuditAction.CREATE,
    "PUT": AuditAction.UPDATE,
    "PATCH": AuditAction.UPDATE,
    "DELETE": AuditAction.DELETE,
}

# Map URL path prefixes to resource types
PATH_TO_RESOURCE_TYPE: dict[str, ResourceType] = {
    "/animals": ResourceType.ANIMAL,
    "/adopters": ResourceType.ADOPTER,
    "/adoption-requests": ResourceType.ADOPTION_REQUEST,
    "/donors": ResourceType.DONOR,
    "/donations": ResourceType.DONATION,
    "/auth": ResourceType.USER,
}


class AuditLog(Base):
    """Immutable audit log entry recording a single authenticated action.

    Attributes:
        id: Auto-incrementing primary key.
        user_id: UUID of the authenticated user who performed the action.
        action: The type of action performed (create, update, delete, etc.).
        resource_type: The type of resource acted upon.
        resource_id: The identifier of the specific resource (UUID string or None).
        timestamp: UTC datetime when the action occurred.
        ip_address: Client IP address (may be proxied).
        user_agent: Client user-agent header value.
        http_method: The HTTP method of the request.
        path: The full request path.
        status_code: The HTTP response status code.
        old_values: Optional JSON snapshot of previous state (for updates/deletes).
        new_values: Optional JSON snapshot of new state (for creates/updates).
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        sa.BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
    )
    resource_type: Mapped[str] = mapped_column(
        sa.String(50),
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
        index=True,
    )
    ip_address: Mapped[str | None] = mapped_column(
        sa.String(45),
        nullable=True,
    )
    user_agent: Mapped[str | None] = mapped_column(
        sa.String(500),
        nullable=True,
    )
    http_method: Mapped[str] = mapped_column(
        sa.String(10),
        nullable=False,
    )
    path: Mapped[str] = mapped_column(
        sa.String(500),
        nullable=False,
    )
    status_code: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
    )
    old_values: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    new_values: Mapped[dict | None] = mapped_column(
        JSONB,
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
    )
