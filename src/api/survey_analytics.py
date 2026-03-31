"""Survey results analytics API.

Provides aggregated survey response data for dashboards and reports.
Supports per-question breakdowns, response trends, and export.
"""

from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/admin/surveys", tags=["survey-analytics"])


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMPLETION_RATE_PRECISION: int = 1
PERCENTAGE_PRECISION: int = 1
MAX_EXPORT_ROWS: int = 10_000
MIN_RESPONSES_FOR_TREND: int = 2
TREND_PERIOD_DAYS: int = 7


class ExportFormat(enum.StrEnum):
    """Supported export formats."""

    CSV = "csv"
    JSON = "json"


class TrendDirection(enum.StrEnum):
    """Response trend direction."""

    UP = "up"
    DOWN = "down"
    STABLE = "stable"


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class ChoiceBreakdown(BaseModel):
    """Breakdown of a single choice option."""

    option: str
    count: int = 0
    percentage: float = 0.0


class QuestionAnalytics(BaseModel):
    """Analytics for a single survey question."""

    question_id: str
    question_text: str
    question_type: str
    total_answers: int = 0
    choice_breakdown: list[ChoiceBreakdown] = Field(default_factory=list)
    text_responses: list[str] = Field(default_factory=list)
    average_rating: float | None = None


class ResponseTrend(BaseModel):
    """Response trend data point."""

    period: str
    count: int = 0


class SurveyAnalyticsSummary(BaseModel):
    """Top-level survey analytics summary."""

    survey_id: str
    survey_title: str
    total_responses: int = 0
    completion_rate: float = 0.0
    average_time_display: str = "N/A"
    questions: list[QuestionAnalytics] = Field(default_factory=list)
    response_trends: list[ResponseTrend] = Field(default_factory=list)
    trend_direction: str = TrendDirection.STABLE
    last_response_at: str | None = None
    generated_at: str = ""


class ExportResult(BaseModel):
    """Result of an export operation."""

    format: str
    row_count: int = 0
    data: list[dict[str, Any]] = Field(default_factory=list)
    generated_at: str = ""


# ---------------------------------------------------------------------------
# In-memory store (shared with public_survey via import)
# ---------------------------------------------------------------------------

# We import the stores from public_survey to aggregate real response data.
# For the analytics module's own testability, we also maintain local references.

_analytics_cache: dict[str, dict[str, Any]] = {}


def _get_survey_store() -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """Import survey data from the public survey module.

    Returns (surveys_dict, responses_list).
    """
    try:
        from src.api.public_survey import _responses, _sample_surveys

        return _sample_surveys, _responses
    except ImportError:
        return {}, []


def _reset_cache() -> None:
    """Clear analytics cache — used in tests."""
    _analytics_cache.clear()


# ---------------------------------------------------------------------------
# Analytics computation
# ---------------------------------------------------------------------------


def compute_question_analytics(
    question: dict[str, Any],
    responses: list[dict[str, Any]],
    survey_id: str,
) -> QuestionAnalytics:
    """Compute analytics for a single question from response data."""
    q_id = question.get("id", "")
    q_text = question.get("text", "")
    q_type = question.get("type", "text")
    options = question.get("options", [])

    # Gather answers for this question across all responses
    answers: list[Any] = []
    for resp in responses:
        if resp.get("survey_id") != survey_id:
            continue
        resp_answers = resp.get("answers", {})
        if q_id in resp_answers:
            answers.append(resp_answers[q_id])

    total_answers = len(answers)
    choice_breakdown: list[ChoiceBreakdown] = []
    text_responses: list[str] = []
    average_rating: float | None = None

    if q_type in ("single_choice", "yes_no"):
        # Count occurrences of each option
        counts: dict[str, int] = {}
        for opt in options:
            label = opt.get("label", opt.get("value", ""))
            counts[label] = 0
        for ans in answers:
            ans_str = str(ans)
            if ans_str in counts:
                counts[ans_str] += 1
            else:
                counts[ans_str] = counts.get(ans_str, 0) + 1
        for label, count in counts.items():
            pct = (
                round(count / total_answers * 100, PERCENTAGE_PRECISION)
                if total_answers > 0
                else 0.0
            )
            choice_breakdown.append(ChoiceBreakdown(option=label, count=count, percentage=pct))

    elif q_type == "multiple_choice":
        counts = {}
        for opt in options:
            label = opt.get("label", opt.get("value", ""))
            counts[label] = 0
        for ans in answers:
            selected = ans if isinstance(ans, list) else [ans]
            for sel in selected:
                sel_str = str(sel)
                if sel_str in counts:
                    counts[sel_str] += 1
                else:
                    counts[sel_str] = counts.get(sel_str, 0) + 1
        for label, count in counts.items():
            pct = (
                round(count / total_answers * 100, PERCENTAGE_PRECISION)
                if total_answers > 0
                else 0.0
            )
            choice_breakdown.append(ChoiceBreakdown(option=label, count=count, percentage=pct))

    elif q_type == "rating":
        numeric_answers = [a for a in answers if isinstance(a, (int, float))]
        if numeric_answers:
            average_rating = round(
                sum(numeric_answers) / len(numeric_answers), PERCENTAGE_PRECISION
            )
        # Build breakdown for each rating value (1-5 typical)
        rating_range = range(1, 6)
        for val in rating_range:
            count = sum(1 for a in numeric_answers if a == val)
            pct = (
                round(count / len(numeric_answers) * 100, PERCENTAGE_PRECISION)
                if numeric_answers
                else 0.0
            )
            choice_breakdown.append(ChoiceBreakdown(option=str(val), count=count, percentage=pct))

    elif q_type == "text":
        text_responses = [str(a) for a in answers[:50]]  # Cap at 50 for display

    return QuestionAnalytics(
        question_id=q_id,
        question_text=q_text,
        question_type=q_type,
        total_answers=total_answers,
        choice_breakdown=choice_breakdown,
        text_responses=text_responses,
        average_rating=average_rating,
    )


def compute_response_trends(
    responses: list[dict[str, Any]],
    survey_id: str,
) -> tuple[list[ResponseTrend], str]:
    """Compute weekly response trends.

    Returns (trends_list, trend_direction).
    """
    # Group responses by week
    weekly: dict[str, int] = {}
    for resp in responses:
        if resp.get("survey_id") != survey_id:
            continue
        submitted = resp.get("submitted_at", "")
        if submitted:
            # Extract YYYY-WNN week key
            try:
                dt = datetime.fromisoformat(submitted)
                week_key = f"{dt.year}-S{dt.isocalendar()[1]:02d}"
                weekly[week_key] = weekly.get(week_key, 0) + 1
            except (ValueError, TypeError):
                pass

    trends = [ResponseTrend(period=k, count=v) for k, v in sorted(weekly.items())]

    direction = TrendDirection.STABLE
    if len(trends) >= MIN_RESPONSES_FOR_TREND:
        last_two = trends[-2:]
        if last_two[1].count > last_two[0].count:
            direction = TrendDirection.UP
        elif last_two[1].count < last_two[0].count:
            direction = TrendDirection.DOWN

    return trends, direction


def generate_survey_analytics(survey_id: str) -> SurveyAnalyticsSummary:
    """Generate complete analytics for a survey."""
    surveys, responses = _get_survey_store()

    survey = surveys.get(survey_id)
    if survey is None:
        msg = f"Survey '{survey_id}' not found"
        raise ValueError(msg)

    survey_responses = [r for r in responses if r.get("survey_id") == survey_id]
    total_responses = len(survey_responses)

    # Completion rate: responses with all required questions answered
    questions = survey.get("questions", [])
    required_ids = [q["id"] for q in questions if q.get("required", False)]
    complete_count = 0
    for resp in survey_responses:
        resp_answers = resp.get("answers", {})
        if all(qid in resp_answers for qid in required_ids):
            complete_count += 1

    completion_rate = (
        round(complete_count / total_responses * 100, COMPLETION_RATE_PRECISION)
        if total_responses > 0
        else 0.0
    )

    # Question analytics
    question_analytics = [compute_question_analytics(q, responses, survey_id) for q in questions]

    # Trends
    trends, direction = compute_response_trends(responses, survey_id)

    # Last response timestamp
    last_response_at: str | None = None
    if survey_responses:
        timestamps = [r.get("submitted_at", "") for r in survey_responses if r.get("submitted_at")]
        if timestamps:
            last_response_at = max(timestamps)

    return SurveyAnalyticsSummary(
        survey_id=survey_id,
        survey_title=survey.get("title", ""),
        total_responses=total_responses,
        completion_rate=completion_rate,
        questions=question_analytics,
        response_trends=trends,
        trend_direction=direction,
        last_response_at=last_response_at,
        generated_at=datetime.now(tz=UTC).isoformat(),
    )


def export_survey_responses(
    survey_id: str,
    fmt: ExportFormat = ExportFormat.JSON,
) -> ExportResult:
    """Export survey responses in requested format."""
    surveys, responses = _get_survey_store()

    survey = surveys.get(survey_id)
    if survey is None:
        msg = f"Survey '{survey_id}' not found"
        raise ValueError(msg)

    survey_responses = [r for r in responses if r.get("survey_id") == survey_id]
    capped = survey_responses[:MAX_EXPORT_ROWS]

    rows: list[dict[str, Any]] = []
    for resp in capped:
        row: dict[str, Any] = {
            "response_id": resp.get("id", ""),
            "submitted_at": resp.get("submitted_at", ""),
        }
        answers = resp.get("answers", {})
        for q in survey.get("questions", []):
            q_id = q.get("id", "")
            q_text = q.get("text", q_id)
            row[q_text] = answers.get(q_id, "")
        rows.append(row)

    return ExportResult(
        format=fmt,
        row_count=len(rows),
        data=rows,
        generated_at=datetime.now(tz=UTC).isoformat(),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/{survey_id}/analytics")
async def get_survey_analytics(
    survey_id: str = Path(..., description="Survey identifier"),
) -> dict[str, Any]:
    """Get aggregated analytics for a survey.

    Returns question breakdowns, completion rate, and response trends.
    """
    try:
        summary = generate_survey_analytics(survey_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return summary.model_dump()


@router.get("/{survey_id}/export")
async def export_responses(
    survey_id: str = Path(..., description="Survey identifier"),
    fmt: ExportFormat = Query(
        default=ExportFormat.JSON, alias="format", description="Export format"
    ),
) -> dict[str, Any]:
    """Export survey responses for download."""
    try:
        result = export_survey_responses(survey_id, fmt)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return result.model_dump()


@router.get("/{survey_id}/summary")
async def get_quick_summary(
    survey_id: str = Path(..., description="Survey identifier"),
) -> dict[str, Any]:
    """Quick summary with just total responses and completion rate."""
    try:
        summary = generate_survey_analytics(survey_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "survey_id": summary.survey_id,
        "survey_title": summary.survey_title,
        "total_responses": summary.total_responses,
        "completion_rate": summary.completion_rate,
        "trend_direction": summary.trend_direction,
        "last_response_at": summary.last_response_at,
    }
