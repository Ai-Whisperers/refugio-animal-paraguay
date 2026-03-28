"""SQLAlchemy ORM models for configurable adoption pipeline stages.

Allows shelters to define custom pipeline stages for their adoption
workflow (e.g., Application Review -> Home Visit -> Trial Period -> Final Approval).
"""

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class AdoptionPipelineStage(Base):
    """Configurable stage in the adoption pipeline.

    Stages are ordered by `position` and define the workflow an adoption
    request moves through. Shelters can customise the pipeline by
    adding, reordering, or disabling stages.
    """

    __tablename__ = "adoption_pipeline_stages"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    name: Mapped[str] = mapped_column(
        sa.String(100),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        sa.Text,
        nullable=True,
    )
    # Order in the pipeline (1-based)
    position: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
    )
    # Whether this stage is currently active in the pipeline
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("true"),
    )
    # Whether this stage requires manual approval to advance
    requires_approval: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("true"),
    )
    # Optional maximum days an adoption can stay in this stage
    max_days: Mapped[int | None] = mapped_column(
        sa.Integer,
        nullable=True,
    )
    # Color for UI display (hex code)
    color: Mapped[str] = mapped_column(
        sa.String(7),
        nullable=False,
        server_default="'#6B7280'",
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

    __table_args__ = (
        sa.UniqueConstraint("name", name="uq_pipeline_stage_name"),
        sa.UniqueConstraint("position", name="uq_pipeline_stage_position"),
        sa.CheckConstraint("position > 0", name="chk_pipeline_stage_position"),
        sa.CheckConstraint(
            "max_days IS NULL OR max_days > 0",
            name="chk_pipeline_stage_max_days",
        ),
    )
