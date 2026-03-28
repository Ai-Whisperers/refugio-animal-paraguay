"""SQLAlchemy ORM model for adoption stage transition history.

Records every stage transition an adoption request goes through,
providing a complete audit trail of the adoption pipeline workflow.
"""

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class AdoptionStageLog(Base):
    """Audit log entry for an adoption request stage transition.

    Each row records a single move from one pipeline stage to another,
    including who triggered the transition and any notes.
    """

    __tablename__ = "adoption_stage_logs"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    adoption_request_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey(
            "adoption_requests.id",
            name="fk_stage_logs_adoption_request_id",
        ),
        nullable=False,
    )
    from_stage_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey(
            "adoption_pipeline_stages.id",
            name="fk_stage_logs_from_stage_id",
        ),
        nullable=True,
    )
    to_stage_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey(
            "adoption_pipeline_stages.id",
            name="fk_stage_logs_to_stage_id",
        ),
        nullable=True,
    )
    # "advance", "reject", "reset"
    action: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(
        sa.Text,
        nullable=True,
    )
    transitioned_by: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", name="fk_stage_logs_transitioned_by"),
        nullable=True,
    )
    transitioned_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    __table_args__ = (
        sa.Index(
            "ix_stage_logs_adoption_request",
            "adoption_request_id",
            "transitioned_at",
        ),
    )
