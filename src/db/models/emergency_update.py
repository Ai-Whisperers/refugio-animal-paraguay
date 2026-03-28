"""EmergencyUpdate model -- progress updates on emergency cases."""

import enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.dialects.postgresql import JSON, TIMESTAMP, UUID
from sqlalchemy.sql import func

from src.db.base import Base


class EmergencyOutcome(enum.StrEnum):
    """Possible outcomes when resolving an emergency case."""

    RECOVERED = "recovered"
    ADOPTED = "adopted"
    IN_CARE = "in_care"
    DECEASED = "deceased"
    OTHER = "other"


class EmergencyUpdate(Base):
    """Progress update posted on an emergency case."""

    __tablename__ = "emergency_updates"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    emergency_id = Column(
        UUID(as_uuid=True),
        ForeignKey("emergency_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text = Column(String(1000), nullable=False)
    photos = Column(JSON, nullable=False, server_default="'[]'::jsonb")
    posted_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_resolution = Column(Boolean, nullable=False, server_default="false")
    outcome = Column(String(20), nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint("length(text) >= 1", name="chk_emergency_update_text_not_empty"),
        CheckConstraint("length(text) <= 1000", name="chk_emergency_update_text_max_len"),
        CheckConstraint(
            "outcome IS NULL OR outcome IN ('recovered', 'adopted', 'in_care', 'deceased', 'other')",
            name="chk_emergency_update_outcome_valid",
        ),
        Index("ix_emergency_updates_created_at", "created_at"),
    )
