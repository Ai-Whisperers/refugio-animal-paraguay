"""SQLAlchemy ORM model for users (staff, admin, and public accounts)."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class UserRole(StrEnum):
    """User role values — must match chk_users_role CHECK constraint exactly."""

    STAFF = "staff"
    ADMIN = "admin"
    VET = "vet"
    ADOPTER = "adopter"
    DONOR = "donor"
    VOLUNTEER = "volunteer"
    FOSTER = "foster"


# Roles available for public self-registration
PUBLIC_REGISTRATION_ROLES = frozenset(
    {UserRole.ADOPTER, UserRole.DONOR, UserRole.VOLUNTEER, UserRole.FOSTER}
)


class User(Base):
    """User account with hashed password and role (staff, admin, or public)."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    full_name: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    email: Mapped[str] = mapped_column(sa.String(255), nullable=False, unique=True)
    phone: Mapped[str | None] = mapped_column(sa.String(20), nullable=True, unique=True)
    hashed_password: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    oauth_provider: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    oauth_id: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    profile_picture_url: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    role: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        server_default="staff",
    )
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.true())
    email_verified: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.false()
    )
    phone_verified: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.false()
    )
    phone_verified_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default=sa.text("0")
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
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
    # Two-factor authentication (TOTP via RFC 6238)
    totp_secret: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.false()
    )
