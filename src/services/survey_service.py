"""Service layer for survey management.

Handles survey CRUD, response submission, validation, and duplicate prevention.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.survey import (
    VALID_QUESTION_TYPES,
    Survey,
    SurveyResponse,
)

logger = logging.getLogger(__name__)

# Pagination defaults
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class SurveyError(Exception):
    """Base error for survey operations."""


class SurveyNotFoundError(SurveyError):
    """Raised when a survey does not exist."""


class SurveyNotActiveError(SurveyError):
    """Raised when attempting to respond to an inactive or expired survey."""


class DuplicateResponseError(SurveyError):
    """Raised when a respondent has already submitted a response."""


class InvalidQuestionsError(SurveyError):
    """Raised when question schema validation fails."""


def validate_questions(questions: list[dict]) -> None:
    """Validate the questions JSON array structure.

    Each question must have:
    - type: one of radio, checkbox, text, rating
    - question: non-empty string
    - options: non-empty list (required for radio and checkbox types)
    """
    if not questions:
        raise InvalidQuestionsError("Survey must have at least one question")

    for idx, q in enumerate(questions):
        if not isinstance(q, dict):
            raise InvalidQuestionsError(f"Question {idx} must be an object")

        q_type = q.get("type")
        if q_type not in VALID_QUESTION_TYPES:
            raise InvalidQuestionsError(
                f"Question {idx}: invalid type '{q_type}', must be one of {VALID_QUESTION_TYPES}"
            )

        question_text = q.get("question")
        if not question_text or not isinstance(question_text, str):
            raise InvalidQuestionsError(
                f"Question {idx}: 'question' field is required and must be a string"
            )

        if q_type in ("radio", "checkbox"):
            options = q.get("options")
            if not options or not isinstance(options, list) or len(options) == 0:
                raise InvalidQuestionsError(
                    f"Question {idx}: '{q_type}' type requires a non-empty 'options' array"
                )


async def create_survey(
    db: AsyncSession,
    title: str,
    questions: list[dict],
    created_by: UUID,
    description: str | None = None,
    is_active: bool = False,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict:
    """Create a new survey with validated questions."""
    validate_questions(questions)

    survey = Survey(
        title=title,
        description=description,
        questions=questions,
        is_active=is_active,
        start_date=start_date,
        end_date=end_date,
        created_by=created_by,
    )
    db.add(survey)
    await db.flush()
    await db.refresh(survey)

    return _survey_to_dict(survey)


async def get_survey(db: AsyncSession, survey_id: UUID) -> dict:
    """Get a single survey by ID."""
    result = await db.execute(select(Survey).where(Survey.id == survey_id))
    survey = result.scalar_one_or_none()
    if survey is None:
        raise SurveyNotFoundError(f"Survey {survey_id} not found")
    return _survey_to_dict(survey)


async def list_surveys(
    db: AsyncSession,
    limit: int = DEFAULT_PAGE_SIZE,
    offset: int = 0,
) -> dict:
    """List surveys with pagination."""
    count_result = await db.execute(select(func.count()).select_from(Survey))
    total = count_result.scalar_one()

    result = await db.execute(
        select(Survey).order_by(Survey.created_at.desc()).limit(limit).offset(offset)
    )
    surveys = list(result.scalars().all())

    return {
        "surveys": [_survey_to_dict(s) for s in surveys],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


async def update_survey(
    db: AsyncSession,
    survey_id: UUID,
    title: str | None = None,
    description: str | None = None,
    questions: list[dict] | None = None,
    is_active: bool | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict:
    """Update an existing survey."""
    result = await db.execute(select(Survey).where(Survey.id == survey_id))
    survey = result.scalar_one_or_none()
    if survey is None:
        raise SurveyNotFoundError(f"Survey {survey_id} not found")

    if questions is not None:
        validate_questions(questions)
        survey.questions = questions

    if title is not None:
        survey.title = title
    if description is not None:
        survey.description = description
    if is_active is not None:
        survey.is_active = is_active
    if start_date is not None:
        survey.start_date = start_date
    if end_date is not None:
        survey.end_date = end_date

    await db.flush()
    await db.refresh(survey)

    return _survey_to_dict(survey)


async def delete_survey(db: AsyncSession, survey_id: UUID) -> None:
    """Delete a survey and all its responses."""
    result = await db.execute(select(Survey).where(Survey.id == survey_id))
    survey = result.scalar_one_or_none()
    if survey is None:
        raise SurveyNotFoundError(f"Survey {survey_id} not found")

    await db.delete(survey)
    await db.flush()


async def submit_response(
    db: AsyncSession,
    survey_id: UUID,
    answers: dict,
    respondent_email: str | None = None,
    respondent_user_id: UUID | None = None,
) -> dict:
    """Submit a response to a survey.

    Validates that the survey is active and within date range.
    Prevents duplicate responses per email per survey.
    """
    # Fetch survey
    result = await db.execute(select(Survey).where(Survey.id == survey_id))
    survey = result.scalar_one_or_none()
    if survey is None:
        raise SurveyNotFoundError(f"Survey {survey_id} not found")

    # Check active status
    if not survey.is_active:
        raise SurveyNotActiveError("Survey is not active")

    # Check date range
    now = datetime.now(UTC)
    if survey.start_date and now < survey.start_date:
        raise SurveyNotActiveError("Survey has not started yet")
    if survey.end_date and now > survey.end_date:
        raise SurveyNotActiveError("Survey has ended")

    # Check duplicate by email
    if respondent_email:
        dup_result = await db.execute(
            select(func.count())
            .select_from(SurveyResponse)
            .where(
                SurveyResponse.survey_id == survey_id,
                SurveyResponse.respondent_email == respondent_email,
            )
        )
        if dup_result.scalar_one() > 0:
            raise DuplicateResponseError(
                f"A response from {respondent_email} already exists for this survey"
            )

    response = SurveyResponse(
        survey_id=survey_id,
        respondent_email=respondent_email,
        respondent_user_id=respondent_user_id,
        answers=answers,
    )
    db.add(response)
    await db.flush()
    await db.refresh(response)

    return _response_to_dict(response)


def _survey_to_dict(survey: Survey) -> dict:
    """Convert a Survey model to a dict."""
    return {
        "id": survey.id,
        "title": survey.title,
        "description": survey.description,
        "questions": survey.questions,
        "is_active": survey.is_active,
        "start_date": survey.start_date,
        "end_date": survey.end_date,
        "created_by": survey.created_by,
        "created_at": survey.created_at,
        "updated_at": survey.updated_at,
    }


def _response_to_dict(response: SurveyResponse) -> dict:
    """Convert a SurveyResponse model to a dict."""
    return {
        "id": response.id,
        "survey_id": response.survey_id,
        "respondent_email": response.respondent_email,
        "respondent_user_id": response.respondent_user_id,
        "answers": response.answers,
        "created_at": response.created_at,
    }
