"""Public survey response collection API.

Allows anonymous users to view active surveys and submit responses.
No authentication required.
"""

from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/surveys", tags=["public-surveys"])


# ---------------------------------------------------------------------------
# Constants & enums
# ---------------------------------------------------------------------------

MAX_RESPONSES_PER_SURVEY: int = 10_000
MAX_TEXT_RESPONSE_LENGTH: int = 2000


class QuestionType(enum.StrEnum):
    """Supported question types."""

    TEXT = "text"
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    RATING = "rating"
    YES_NO = "yes_no"


class SurveyStatus(enum.StrEnum):
    """Survey lifecycle status."""

    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class QuestionOption(BaseModel):
    """Option for choice-type questions."""

    id: str
    text: str


class SurveyQuestion(BaseModel):
    """Single question in a survey."""

    id: str
    text: str
    question_type: QuestionType
    required: bool = True
    options: list[QuestionOption] = Field(default_factory=list)
    min_rating: int = 1
    max_rating: int = 5


class PublicSurvey(BaseModel):
    """Survey as seen by public respondents."""

    id: str
    title: str
    description: str
    questions: list[SurveyQuestion]
    thank_you_message: str
    estimated_minutes: int
    response_count: int
    is_active: bool


class AnswerInput(BaseModel):
    """Single answer to a survey question."""

    question_id: str = Field(min_length=1)
    value: str | int | list[str]


class SurveyResponseSubmit(BaseModel):
    """Survey response submission."""

    respondent_name: str = Field(default="", max_length=100)
    respondent_email: str = Field(default="", max_length=200)
    answers: list[AnswerInput] = Field(min_length=1)


class SurveyResponseResult(BaseModel):
    """Response submission result."""

    success: bool
    message: str
    response_id: str
    survey_id: str


# ---------------------------------------------------------------------------
# Sample data (MVP)
# ---------------------------------------------------------------------------

_sample_surveys: dict[str, dict[str, Any]] = {
    "survey-satisfaccion": {
        "id": "survey-satisfaccion",
        "title": "Encuesta de Satisfaccion",
        "description": "Ayudanos a mejorar nuestros servicios compartiendo tu experiencia.",
        "status": "active",
        "thank_you_message": "Gracias por completar la encuesta. Tu opinion es muy importante para nosotros.",
        "estimated_minutes": 5,
        "response_count": 0,
        "questions": [
            {
                "id": "q1",
                "text": "Como calificarias tu experiencia general con Refugio Animal?",
                "question_type": "rating",
                "required": True,
                "options": [],
                "min_rating": 1,
                "max_rating": 5,
            },
            {
                "id": "q2",
                "text": "Que servicio utilizaste?",
                "question_type": "single_choice",
                "required": True,
                "options": [
                    {"id": "opt1", "text": "Adopcion"},
                    {"id": "opt2", "text": "Donacion"},
                    {"id": "opt3", "text": "Voluntariado"},
                    {"id": "opt4", "text": "Consulta veterinaria"},
                    {"id": "opt5", "text": "Otro"},
                ],
                "min_rating": 1,
                "max_rating": 5,
            },
            {
                "id": "q3",
                "text": "Que aspectos podemos mejorar?",
                "question_type": "multiple_choice",
                "required": False,
                "options": [
                    {"id": "imp1", "text": "Atencion al cliente"},
                    {"id": "imp2", "text": "Proceso de adopcion"},
                    {"id": "imp3", "text": "Sitio web"},
                    {"id": "imp4", "text": "Comunicacion"},
                    {"id": "imp5", "text": "Horarios"},
                ],
                "min_rating": 1,
                "max_rating": 5,
            },
            {
                "id": "q4",
                "text": "Recomendarias Refugio Animal a un amigo?",
                "question_type": "yes_no",
                "required": True,
                "options": [],
                "min_rating": 1,
                "max_rating": 5,
            },
            {
                "id": "q5",
                "text": "Comentarios adicionales",
                "question_type": "text",
                "required": False,
                "options": [],
                "min_rating": 1,
                "max_rating": 5,
            },
        ],
    },
}

_responses: list[dict[str, Any]] = []
_next_response_id: int = 1


def _reset_store() -> None:
    """Reset store for testing."""
    global _next_response_id
    _responses.clear()
    _next_response_id = 1
    for survey in _sample_surveys.values():
        survey["response_count"] = 0


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/active",
    response_model=list[PublicSurvey],
    summary="List active surveys",
)
async def list_active_surveys() -> list[PublicSurvey]:
    """Return all active surveys available for responses."""
    return [
        PublicSurvey(**{k: v for k, v in s.items() if k != "status"}, is_active=True)
        for s in _sample_surveys.values()
        if s["status"] == "active"
    ]


@router.get(
    "/{survey_id}",
    response_model=PublicSurvey,
    summary="Get survey details",
)
async def get_survey(
    survey_id: str = Path(description="Survey ID"),
) -> PublicSurvey:
    """Get a single survey by ID for rendering the form."""
    survey = _sample_surveys.get(survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada")

    if survey["status"] != "active":
        raise HTTPException(status_code=410, detail="Esta encuesta ya no esta activa")

    return PublicSurvey(**{k: v for k, v in survey.items() if k != "status"}, is_active=True)


@router.post(
    "/{survey_id}/responses",
    response_model=SurveyResponseResult,
    status_code=201,
    summary="Submit survey response",
)
async def submit_survey_response(
    survey_id: str = Path(description="Survey ID"),
    body: SurveyResponseSubmit = ...,
) -> SurveyResponseResult:
    """Submit a response to an active survey."""
    global _next_response_id

    survey = _sample_surveys.get(survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada")

    if survey["status"] != "active":
        raise HTTPException(status_code=410, detail="Esta encuesta ya no esta activa")

    if survey["response_count"] >= MAX_RESPONSES_PER_SURVEY:
        raise HTTPException(
            status_code=409,
            detail="Esta encuesta ha alcanzado el limite de respuestas",
        )

    # Validate required questions answered
    answered_ids = {a.question_id for a in body.answers}

    for q in survey["questions"]:
        if q["required"] and q["id"] not in answered_ids:
            raise HTTPException(
                status_code=422,
                detail=f"Pregunta obligatoria sin respuesta: {q['text']}",
            )

    response_id = f"resp-{_next_response_id}"
    _next_response_id += 1

    _responses.append(
        {
            "id": response_id,
            "survey_id": survey_id,
            "respondent_name": body.respondent_name,
            "respondent_email": body.respondent_email,
            "answers": [{"question_id": a.question_id, "value": a.value} for a in body.answers],
            "submitted_at": datetime.now(UTC).isoformat(),
        }
    )
    survey["response_count"] += 1

    return SurveyResponseResult(
        success=True,
        message="Respuesta registrada exitosamente",
        response_id=response_id,
        survey_id=survey_id,
    )


@router.get(
    "/{survey_id}/response-count",
    summary="Get response count",
)
async def get_response_count(
    survey_id: str = Path(description="Survey ID"),
) -> dict[str, Any]:
    """Return the number of responses for a survey."""
    survey = _sample_surveys.get(survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada")

    return {
        "survey_id": survey_id,
        "response_count": survey["response_count"],
    }
