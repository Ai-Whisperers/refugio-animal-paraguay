"""SQLAlchemy ORM model for castration campaign photos.

Before/after/recovery photos uploaded by clinics when redeeming
castration vouchers. Photos with public_consent=True appear in
the campaign gallery.
"""

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base

VALID_PHOTO_TYPES = {"before", "after", "recovery"}


class CastrationPhoto(Base):
    """Photo evidence for a completed castration surgery.

    Linked to a vet voucher (which links to campaign + animal info).
    Clinics upload 1-3 photos per redemption. Only photos with
    public_consent=True are shown in the public gallery.
    """

    __tablename__ = "castration_photos"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    vet_voucher_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("vet_vouchers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    campaign_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("castration_campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    photo_url: Mapped[str] = mapped_column(sa.String(500), nullable=False)
    photo_type: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        comment="before | after | recovery",
    )
    animal_name: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    animal_species: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    public_consent: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.false()
    )
    is_featured: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.false()
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
