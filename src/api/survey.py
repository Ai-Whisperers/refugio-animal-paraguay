"""API endpoints for survey management.

Admin endpoints for CRUD operations on surveys, and a public endpoint
for submitting survey responses.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin, require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.services.survey_service import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    DuplicateResponseError,
    InvalidQuestionsError,
    SurveyNotActiveError,
    SurveyNotFoundError,
    create_survey,
    delete_survey,
    get_survey,
    list_surveys,
    submit_response,
    update_survey,
)

admin_router = APIRouter(tags=["Surveys (Admin)"])
public_router = APIRouter(tags=["Surveys (Public)"])


# --- Schemas ---


class QuestionSchema(BaseModel):
    """A single survey question."""

    type: str
    question: str
    options: list[str] | None = None


class CreateSurveyRequest(BaseModel):
    """Request body for creating a survey."""

    title: str
    description: str | None = None
    questions: list[dict]
    is_active: bool = False
    start_date: datetime | None = None
    end_date: datetime | None = None


class UpdateSurveyRequest(BaseModel):
    """Request body for updating a survey."""

    title: str | None = None
    description: str | None = None
    questions: list[dict] | None = None
    is_active: bool | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


class SurveyResponse(BaseModel):
    """Survey details response."""

    id: UUID
    title: str
    description: str | None = None
    questions: list[dict]
    is_active: bool
    start_date: datetime | None = None
    end_date: datetime | None = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SurveyListResponse(BaseModel):
    """Paginated list of surveys."""

    surveys: list[SurveyResponse]
    total: int
    limit: int
    offset: int


class SubmitResponseRequest(BaseModel):
    """Request body for submitting a survey response."""

    answers: dict
    respondent_email: str | None = None


class ResponseSubmittedResponse(BaseModel):
    """Confirmation of submitted response."""

    id: UUID
    survey_id: UUID
    respondent_email: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Admin Endpoints ---


@admin_router.post(
    "/api/admin/surveys",
    response_model=SurveyResponse,
    status_code=201,
)
async def create_survey_endpoint(
    body: CreateSurveyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """Create a new survey."""
    try:
        return await create_survey(
            db=db,
            title=body.title,
            description=body.description,
            questions=body.questions,
            is_active=body.is_active,
            start_date=body.start_date,
            end_date=body.end_date,
            created_by=current_user.id,
        )
    except InvalidQuestionsError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None


@admin_router.get(
    "/api/admin/surveys",
    response_model=SurveyListResponse,
)
async def list_surveys_endpoint(
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> dict:
    """List all surveys with pagination."""
    return await list_surveys(db=db, limit=limit, offset=offset)


@admin_router.get(
    "/api/admin/surveys/{survey_id}",
    response_model=SurveyResponse,
)
async def get_survey_endpoint(
    survey_id: UUID,
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> dict:
    """Get a single survey by ID."""
    try:
        return await get_survey(db=db, survey_id=survey_id)
    except SurveyNotFoundError:
        raise HTTPException(status_code=404, detail="Survey not found") from None


@admin_router.put(
    "/api/admin/surveys/{survey_id}",
    response_model=SurveyResponse,
)
async def update_survey_endpoint(
    survey_id: UUID,
    body: UpdateSurveyRequest,
    db: AsyncSession = Depends(get_db),
    _admin: object = Depends(require_admin),
) -> dict:
    """Update an existing survey."""
    try:
        return await update_survey(
            db=db,
            survey_id=survey_id,
            title=body.title,
            description=body.description,
            questions=body.questions,
            is_active=body.is_active,
            start_date=body.start_date,
            end_date=body.end_date,
        )
    except SurveyNotFoundError:
        raise HTTPException(status_code=404, detail="Survey not found") from None
    except InvalidQuestionsError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None


@admin_router.delete(
    "/api/admin/surveys/{survey_id}",
    status_code=204,
)
async def delete_survey_endpoint(
    survey_id: UUID,
    db: AsyncSession = Depends(get_db),
    _admin: object = Depends(require_admin),
) -> None:
    """Delete a survey and all its responses."""
    try:
        await delete_survey(db=db, survey_id=survey_id)
    except SurveyNotFoundError:
        raise HTTPException(status_code=404, detail="Survey not found") from None


# --- Public Endpoint ---


@public_router.post(
    "/api/surveys/{survey_id}/responses",
    response_model=ResponseSubmittedResponse,
    status_code=201,
)
async def submit_survey_response(
    survey_id: UUID,
    body: SubmitResponseRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Submit a response to a survey (public endpoint)."""
    try:
        return await submit_response(
            db=db,
            survey_id=survey_id,
            answers=body.answers,
            respondent_email=body.respondent_email,
        )
    except SurveyNotFoundError:
        raise HTTPException(status_code=404, detail="Survey not found") from None
    except SurveyNotActiveError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except DuplicateResponseError:
        raise HTTPException(
            status_code=429, detail="You have already submitted a response to this survey"
        ) from None
