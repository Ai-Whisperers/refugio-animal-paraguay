"""Admin survey management API.

Allows administrators to create, update, publish, and clone surveys.
"""

from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/admin/survey-management", tags=["survey-admin"])


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_TITLE_LENGTH: int = 200
MAX_DESCRIPTION_LENGTH: int = 2000
MAX_QUESTIONS_PER_SURVEY: int = 50
MAX_OPTIONS_PER_QUESTION: int = 20
MIN_TITLE_LENGTH: int = 3


class SurveyAdminStatus(enum.StrEnum):
    """Survey lifecycle status."""

    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"


class QuestionType(enum.StrEnum):
    """Supported question types for survey builder."""

    TEXT = "text"
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    RATING = "rating"
    YES_NO = "yes_no"


QUESTION_TYPE_LABELS_ES: dict[str, str] = {
    "text": "Texto libre",
    "single_choice": "Opcion unica",
    "multiple_choice": "Opcion multiple",
    "rating": "Puntuacion",
    "yes_no": "Si / No",
}


# ---------------------------------------------------------------------------
# Request/response schemas
# ---------------------------------------------------------------------------


class QuestionOptionInput(BaseModel):
    """Option for choice-type questions."""

    label: str = Field(..., min_length=1, max_length=200)
    value: str = ""


class QuestionInput(BaseModel):
    """Question definition in the survey builder."""

    text: str = Field(..., min_length=1, max_length=500)
    question_type: QuestionType = QuestionType.TEXT
    required: bool = True
    options: list[QuestionOptionInput] = Field(default_factory=list)
    order: int = 0


class SurveyCreateRequest(BaseModel):
    """Create a new survey."""

    title: str = Field(..., min_length=MIN_TITLE_LENGTH, max_length=MAX_TITLE_LENGTH)
    description: str = Field(default="", max_length=MAX_DESCRIPTION_LENGTH)
    questions: list[QuestionInput] = Field(default_factory=list)
    start_date: str | None = None
    end_date: str | None = None
    status: SurveyAdminStatus = SurveyAdminStatus.DRAFT


class SurveyUpdateRequest(BaseModel):
    """Update an existing survey."""

    title: str | None = None
    description: str | None = None
    questions: list[QuestionInput] | None = None
    start_date: str | None = None
    end_date: str | None = None
    status: SurveyAdminStatus | None = None


class SurveyResponse(BaseModel):
    """Survey response for admin views."""

    id: str
    title: str
    description: str
    status: str
    questions: list[dict[str, Any]]
    start_date: str | None = None
    end_date: str | None = None
    created_at: str
    updated_at: str
    response_count: int = 0


class SurveyListResponse(BaseModel):
    """List of surveys."""

    surveys: list[SurveyResponse]
    total: int


# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

_surveys: dict[str, dict[str, Any]] = {}


def _reset_store() -> None:
    """Clear store — used in tests."""
    _surveys.clear()


def _build_question_dict(q: QuestionInput, idx: int) -> dict[str, Any]:
    """Convert question input to storage dict."""
    return {
        "id": f"q{idx + 1}",
        "text": q.text,
        "type": q.question_type.value,
        "required": q.required,
        "options": [{"label": o.label, "value": o.value or o.label} for o in q.options],
        "order": q.order if q.order > 0 else idx,
    }


def _validate_survey(req: SurveyCreateRequest | SurveyUpdateRequest) -> list[str]:
    """Validate survey data. Returns list of error messages."""
    errors: list[str] = []

    if isinstance(req, SurveyCreateRequest) and len(req.title) < MIN_TITLE_LENGTH:
        errors.append(f"El titulo debe tener al menos {MIN_TITLE_LENGTH} caracteres")

    if hasattr(req, "questions") and req.questions is not None:
        if len(req.questions) > MAX_QUESTIONS_PER_SURVEY:
            errors.append(f"Maximo {MAX_QUESTIONS_PER_SURVEY} preguntas por encuesta")

        for i, q in enumerate(req.questions):
            if q.question_type in (QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE):
                if len(q.options) < 2:
                    errors.append(
                        f"Pregunta {i + 1}: las preguntas de opcion necesitan al menos 2 opciones"
                    )
                if len(q.options) > MAX_OPTIONS_PER_QUESTION:
                    errors.append(f"Pregunta {i + 1}: maximo {MAX_OPTIONS_PER_QUESTION} opciones")

    if (
        hasattr(req, "start_date")
        and hasattr(req, "end_date")
        and req.start_date
        and req.end_date
        and req.start_date > req.end_date
    ):
        errors.append("La fecha de inicio no puede ser posterior a la fecha de fin")

    return errors


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", status_code=201)
async def create_survey(req: SurveyCreateRequest) -> dict[str, Any]:
    """Create a new survey (draft by default)."""
    errors = _validate_survey(req)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})

    survey_id = f"survey-{uuid.uuid4().hex[:8]}"
    now = datetime.now(tz=UTC).isoformat()

    questions = [_build_question_dict(q, i) for i, q in enumerate(req.questions)]

    survey = {
        "id": survey_id,
        "title": req.title,
        "description": req.description,
        "status": req.status.value,
        "questions": questions,
        "start_date": req.start_date,
        "end_date": req.end_date,
        "created_at": now,
        "updated_at": now,
        "response_count": 0,
    }
    _surveys[survey_id] = survey

    return SurveyResponse(**survey).model_dump()


@router.get("")
async def list_surveys(
    status: SurveyAdminStatus | None = None,
) -> dict[str, Any]:
    """List all surveys, optionally filtered by status."""
    surveys = list(_surveys.values())
    if status:
        surveys = [s for s in surveys if s["status"] == status.value]

    responses = [SurveyResponse(**s) for s in surveys]
    return SurveyListResponse(surveys=responses, total=len(responses)).model_dump()


@router.get("/{survey_id}")
async def get_survey(
    survey_id: str = Path(..., description="Survey identifier"),
) -> dict[str, Any]:
    """Get a single survey by ID."""
    survey = _surveys.get(survey_id)
    if survey is None:
        raise HTTPException(status_code=404, detail=f"Encuesta '{survey_id}' no encontrada")
    return SurveyResponse(**survey).model_dump()


@router.put("/{survey_id}")
async def update_survey(
    req: SurveyUpdateRequest,
    survey_id: str = Path(..., description="Survey identifier"),
) -> dict[str, Any]:
    """Update an existing survey."""
    survey = _surveys.get(survey_id)
    if survey is None:
        raise HTTPException(status_code=404, detail=f"Encuesta '{survey_id}' no encontrada")

    errors = _validate_survey(req)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})

    if req.title is not None:
        survey["title"] = req.title
    if req.description is not None:
        survey["description"] = req.description
    if req.questions is not None:
        survey["questions"] = [_build_question_dict(q, i) for i, q in enumerate(req.questions)]
    if req.start_date is not None:
        survey["start_date"] = req.start_date
    if req.end_date is not None:
        survey["end_date"] = req.end_date
    if req.status is not None:
        survey["status"] = req.status.value

    survey["updated_at"] = datetime.now(tz=UTC).isoformat()

    return SurveyResponse(**survey).model_dump()


@router.post("/{survey_id}/publish")
async def publish_survey(
    survey_id: str = Path(..., description="Survey identifier"),
) -> dict[str, Any]:
    """Publish a draft survey, making it active."""
    survey = _surveys.get(survey_id)
    if survey is None:
        raise HTTPException(status_code=404, detail=f"Encuesta '{survey_id}' no encontrada")

    if survey["status"] != SurveyAdminStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden publicar encuestas en estado borrador",
        )

    if not survey.get("questions"):
        raise HTTPException(
            status_code=400,
            detail="La encuesta debe tener al menos una pregunta",
        )

    survey["status"] = SurveyAdminStatus.ACTIVE
    survey["updated_at"] = datetime.now(tz=UTC).isoformat()

    return SurveyResponse(**survey).model_dump()


@router.post("/{survey_id}/clone", status_code=201)
async def clone_survey(
    survey_id: str = Path(..., description="Survey identifier to clone"),
) -> dict[str, Any]:
    """Clone an existing survey as a new draft."""
    original = _surveys.get(survey_id)
    if original is None:
        raise HTTPException(status_code=404, detail=f"Encuesta '{survey_id}' no encontrada")

    new_id = f"survey-{uuid.uuid4().hex[:8]}"
    now = datetime.now(tz=UTC).isoformat()

    cloned = {
        **original,
        "id": new_id,
        "title": f"{original['title']} (Copia)",
        "status": SurveyAdminStatus.DRAFT,
        "created_at": now,
        "updated_at": now,
        "response_count": 0,
    }
    _surveys[new_id] = cloned

    return SurveyResponse(**cloned).model_dump()


@router.post("/{survey_id}/close")
async def close_survey(
    survey_id: str = Path(..., description="Survey identifier"),
) -> dict[str, Any]:
    """Close an active survey."""
    survey = _surveys.get(survey_id)
    if survey is None:
        raise HTTPException(status_code=404, detail=f"Encuesta '{survey_id}' no encontrada")

    if survey["status"] != SurveyAdminStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden cerrar encuestas activas",
        )

    survey["status"] = SurveyAdminStatus.CLOSED
    survey["updated_at"] = datetime.now(tz=UTC).isoformat()

    return SurveyResponse(**survey).model_dump()
