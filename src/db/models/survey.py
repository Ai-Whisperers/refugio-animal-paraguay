"""SQLAlchemy ORM models for surveys and survey responses."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class QuestionType(StrEnum):
    """Valid question types for survey questions."""

    RADIO = "radio"
    CHECKBOX = "checkbox"
    TEXT = "text"
    RATING = "rating"


VALID_QUESTION_TYPES = {qt.value for qt in QuestionType}


class Survey(Base):
    """A survey with flexible JSON-based questions."""

    __tablename__ = "surveys"

    id: Mapped[UUID] = mapped_column(
        sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    title: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    questions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    start_date: Mapped[datetime | None] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=True)
    created_by: Mapped[UUID] = mapped_column(sa.Uuid, sa.ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()
    )

    responses: Mapped[list["SurveyResponse"]] = relationship(
        back_populates="survey", cascade="all, delete-orphan"
    )


class SurveyResponse(Base):
    """A response to a survey from a community member."""

    __tablename__ = "survey_responses"

    id: Mapped[UUID] = mapped_column(
        sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    survey_id: Mapped[UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False
    )
    respondent_email: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    respondent_user_id: Mapped[UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("users.id"), nullable=True
    )
    answers: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), server_default=sa.func.now()
    )

    survey: Mapped["Survey"] = relationship(back_populates="responses")

    __table_args__ = (
        sa.Index("ix_survey_responses_survey_id", "survey_id"),
        sa.UniqueConstraint(
            "survey_id",
            "respondent_email",
            name="uq_survey_responses_survey_email",
        ),
    )
