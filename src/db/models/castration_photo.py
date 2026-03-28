"""SQLAlchemy ORM model for castration campaign photos.

Stores before/after/recovery photos from castration procedures,
linked to campaigns. Photos with public consent can be shown in
the public gallery and impact reports.
"""

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base

VALID_PHOTO_TYPES = {"before", "after", "recovery"}


class CastrationPhoto(Base):
    """Photo from a castration procedure, linked to a campaign."""

    __tablename__ = "castration_photos"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    vet_voucher_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("vet_vouchers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    campaign_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("castration_campaigns.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    photo_url: Mapped[str] = mapped_column(sa.String(500), nullable=False)
    photo_type: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    animal_name: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    animal_species: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    public_consent: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.text("false")
    )
    is_featured: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.text("false")
    )
    uploaded_by_clinic_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("vet_clinics.id", ondelete="SET NULL"),
        nullable=True,
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    __table_args__ = (
        sa.CheckConstraint(
            "photo_type IN ('before', 'after', 'recovery')",
            name="chk_castration_photo_type",
        ),
        sa.Index(
            "ix_castration_photos_campaign_consent",
            "campaign_id",
            "public_consent",
        ),
    )
