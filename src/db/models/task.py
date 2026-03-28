"""SQLAlchemy ORM models for volunteer task assignment and tracking (RAP-185)."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class TaskStatus(StrEnum):
    """Lifecycle status of a task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskCategory(StrEnum):
    """Category of shelter task."""

    FEEDING = "feeding"
    CLEANING = "cleaning"
    WALKING = "walking"
    SOCIALIZATION = "socialization"
    VETERINARY_ASSISTANCE = "veterinary_assistance"
    TRANSPORT = "transport"
    ADMIN = "admin"
    OTHER = "other"


class TaskPriority(StrEnum):
    """Priority level for a task."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


VALID_TASK_STATUSES = {s.value for s in TaskStatus}
VALID_TASK_CATEGORIES = {c.value for c in TaskCategory}
VALID_TASK_PRIORITIES = {p.value for p in TaskPriority}

TASK_TITLE_MAX_LENGTH = 200
TASK_NOTES_MAX_LENGTH = 2000


class Task(Base):
    """A shelter task that can be assigned to a volunteer."""

    __tablename__ = "tasks"

    id: Mapped[UUID] = mapped_column(
        sa.Uuid,
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    created_by: Mapped[UUID] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    assigned_to: Mapped[UUID | None] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        sa.String(TASK_TITLE_MAX_LENGTH),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    category: Mapped[str] = mapped_column(
        sa.String(30),
        nullable=False,
        server_default=sa.text("'other'"),
        index=True,
    )
    priority: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default=sa.text("'medium'"),
        index=True,
    )
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default=sa.text("'pending'"),
        index=True,
    )
    due_date: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
        index=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    completion_notes: Mapped[str | None] = mapped_column(
        sa.String(TASK_NOTES_MAX_LENGTH), nullable=True
    )
    # Optional link to an animal this task is about
    animal_id: Mapped[UUID | None] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("animals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
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
        sa.CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed', 'cancelled')",
            name="chk_task_status_valid",
        ),
        sa.CheckConstraint(
            "category IN ('feeding', 'cleaning', 'walking', 'socialization', "
            "'veterinary_assistance', 'transport', 'admin', 'other')",
            name="chk_task_category_valid",
        ),
        sa.CheckConstraint(
            "priority IN ('low', 'medium', 'high', 'urgent')",
            name="chk_task_priority_valid",
        ),
    )
